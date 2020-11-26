import torch
import numpy as np
import transformers
import torch.nn as nn

from tqdm.autonotebook import tqdm
from config import *
from value import *

import utils
class TweetModel(transformers.BertPreTrainedModel):
    """
    Model class that combines a pretrained bert model with a linear later
    """
    def __init__(self, conf, num_labels):
        super(TweetModel, self).__init__(conf)
        # pretrained BERT model을 불러옵니다.
        self.bert = transformers.BertModel.from_pretrained(config.BERT_PATH, config=conf)
        
        # Set 10% dropout to be applied to the BERT backbone's output
        # dropout은 은닉층에서 일정 확률로 유닛을 사용하지 않도록(=0) 합니다.
        # 따라서 해당 케이스에서는 사용된 유닛만을 이용해 loss를 구하고 grident를 수행합니다.
        # 결국 오버피팅 방지 가능!! (하나의 유닛에 의존하는 현상을 제거)
        self.drop_out = nn.Dropout(0.1)
        
        # 우리가 쓰는 bert-base-uncased 모델은 768의 hidden representation을 가지고 있음
        # 그래서 새로운 레이어를 이어 붙일 때에도 768개씩 붙여야함.
        
        # 우리의 데이터를 추가로 학습하는 용도로 사용할 추가적인 레이어가 필요함. (hidden_layer 추가)
        # 히든 레이어를 추가할수록 복잡한 딥러닝 네트워크를 만들 수 있지만... 데이터가 많이 필요할 듯
        
        # 여기에서는 단어 임베딩 결과를 활용할 수 있게 레이어 정의
        # BERT를 수행하며 나온 hidden layer 12개중, 마지막 10번째 11번째를 사용할 것임.
        # 12번째는 오버피팅 가능성이 높기 때문
        # 따라서 10번째(768) 11번째 (768) 두개의 레이어를 input으로 받을 것이기 때문에 레이어의 input은 768 * 2
        
        # layer0만으로 결과를 내기에는 제대로 학습이 안된다고 판단이 되어 같은 크기의 레이어 layer1를 추가할 예정
        # 따라서 768*2 -> 768*2 레이어 정의
        self.l0 = nn.Linear(768 * 2, 768 * 2)
        
        # l0으로부터 768*2 결과를 전달받아 최종적으로 start, end, class를 판단하기 위한 layer1를 정의
        self.l1 = nn.Linear(768 * 2, 2 + num_labels)
        
        # 사용할 activation 함수
        self.gelu = nn.GELU()
        
        # 가중치 랜덤 초기화
        torch.nn.init.normal_(self.l0.weight, std=0.02)
        torch.nn.init.normal_(self.l1.weight, std=0.02)
    
    def forward(self, ids, mask, token_type_ids, error_index):
        # BERT backbone으로부터 hidden states를 얻어옴.
        _, _, out = self.bert(
            ids,
            attention_mask=mask,
            token_type_ids=token_type_ids
        ) # bert_layers x bs x SL x (768)

        # Concatenate the last two hidden states
        # This is done since experiments have shown that just getting the last layer
        # gives out vectors that may be too taylored to the original BERT training objectives (MLM + NSP)
        # Sample explanation: https://bert-as-service.readthedocs.io/en/latest/section/faq.html#why-not-the-last-hidden-layer-why-second-to-last
        
        # BERT를 수행하며 나온 hidden layer의 output에서 -2번째, -1번째만 가져옴. 그리고 한줄로 이어 붙이기

        error_index = error_index.view(out[-1].shape[0],out[-1].shape[1],1)
        out = torch.cat((out[-1], out[-2]), dim=-1) # bs x SL x (768 * 2)
        
        # 위에서 말했던것 처럼 10%의 노드를 제거
        out = self.drop_out(out) # bs x SL x (768 * 2)
        # The "dropped out" hidden vectors are now fed into the linear layer to output two scores
        
        # 해당 결과를 layer0에 통과
        out = self.l0(out) # bs x SL x 2
        
        # 이 결과를 바로 사용할 것은 아니기에 gelu functaion을 거치게 만듦.
        out = self.gelu(out)
        
        # layer1로 가기 전에도 똑같이 drop oup 진행
        out = self.drop_out(out)
        
        # layer1로 전달
        logits = self.l1(out)
        
        # 현재 layer1은 n개의 output을 내기때문에 이것을 분리
        # (bs x SL x n) -> (bs x SL x 1), (bs x SL x 1) ...
        outputs = list(logits.split(1, dim=-1))
        for i in range(0,len(outputs)):
            outputs[i] = outputs[i].squeeze(-1)
            

        start_logits = outputs[0] # (bs x SL)
        end_logits = outputs[1] # (bs x SL)
        class_logits = outputs[2:]
        return start_logits, end_logits, class_logits


def loss_fn(start_logits, end_logits, class_logits, start_positions, end_positions, class_targets):
    """
    Return the sum of the cross entropy losses for both the start and end logits
    """
    loss_fct = nn.CrossEntropyLoss()
    start_loss = loss_fct(start_logits, start_positions)
    end_loss = loss_fct(end_logits, end_positions)
    total_loss = start_loss + end_loss
        
    class_targets = class_targets.t()

    for i in range(0, len(class_list)):
        total_loss += loss_fct(class_logits[i], class_targets[i]) / len(class_list)
    return total_loss
def train_fn(data_loader, model, optimizer, device, scheduler=None):
    """
    Trains the bert model on the twitter data
    """
    # Set model to training mode (dropout + sampled batch norm is activated)
    model.train()
    losses = utils.AverageMeter()
    jaccards = utils.AverageMeter()

    # Set tqdm to add loading screen and set the length
    tk0 = tqdm(data_loader, total=len(data_loader))
    
    # Train the model on each batch
    for bi, d in enumerate(tk0):

        ids = d["ids"]
        token_type_ids = d["token_type_ids"]
        mask = d["mask"]
        targets_start = d["targets_start"]
        targets_end = d["targets_end"]
        sentiment = d["sentiment"]
        orig_selected = d["orig_selected"]
        orig_tweet = d["orig_tweet"][2]
        offsets = d["offsets"]
        targets_class = d["targets_class"]
        error_index = d["error_index"]

        # Move ids, masks, and targets to gpu while setting as torch.long
        ids = ids.to(device, dtype=torch.long)
        token_type_ids = token_type_ids.to(device, dtype=torch.long)
        mask = mask.to(device, dtype=torch.long)
        targets_start = targets_start.to(device, dtype=torch.long)
        targets_end = targets_end.to(device, dtype=torch.long)
        targets_class = targets_class.to(device, dtype=torch.long)
        error_index = error_index.to(device, dtype=torch.long)
        # Reset gradients
        model.zero_grad()
        # Use ids, masks, and token types as input to the model
        # Predict logits for each of the input tokens for each batch
        outputs_start, outputs_end, outputs_class = model(
            ids=ids,
            mask=mask,
            token_type_ids=token_type_ids,
            error_index=error_index
        ) # (bs x SL), (bs x SL)
        # Calculate batch loss based on CrossEntropy
        loss = loss_fn(outputs_start, outputs_end, outputs_class, targets_start, targets_end, targets_class)
        # Calculate gradients based on loss
        loss.backward()
        # Adjust weights based on calculated gradients
        optimizer.step()
        # Update scheduler
        scheduler.step()
        
        # Apply softmax to the start and end logits
        # This squeezes each of the logits in a sequence to a value between 0 and 1, while ensuring that they sum to 1
        # This is similar to the characteristics of "probabilities"
        outputs_start = torch.softmax(outputs_start, dim=1).cpu().detach().numpy()
        outputs_end = torch.softmax(outputs_end, dim=1).cpu().detach().numpy()
        outputs_class = [torch.softmax(i, dim=1).cpu().detach().numpy() for i in outputs_class]
        
        # Calculate the jaccard score based on the predictions for this batch
        jaccard_scores = []
        for px, tweet in enumerate(orig_tweet):
            selected_tweet = orig_selected[px]
            tweet_sentiment = sentiment[px]
            ont_hot_class = [np.argmax(i[px, :]) for i in outputs_class]
            class_number = ont_hot_class.index(max(ont_hot_class))
            jaccard_score, _ = calculate_jaccard_score(
                original_tweet=tweet, # Full text of the px'th tweet in the batch
                target_string=selected_tweet, # Span containing the specified sentiment for the px'th tweet in the batch
                sentiment_val=tweet_sentiment, # Sentiment of the px'th tweet in the batch
                idx_start=np.argmax(outputs_start[px, :]), # Predicted start index for the px'th tweet in the batch
                idx_end=np.argmax(outputs_end[px, :]), # Predicted end index for the px'th tweet in the batch
                offsets=offsets[px], # Offsets for each of the tokens for the px'th tweet in the batch
                class_number=class_number
            )
            jaccard_scores.append(jaccard_score)
        # Update the jaccard score and loss
        # For details, refer to `AverageMeter` in https://www.kaggle.com/abhishek/utils
        jaccards.update(np.mean(jaccard_scores), ids.size(0))
        losses.update(loss.item(), ids.size(0))
        # Print the average loss and jaccard score at the end of each batch
        tk0.set_postfix(loss=losses.avg, jaccard=jaccards.avg)


def eval_fn(data_loader, model, device):
    """
    Evaluation function to predict on the test set
    """
    # Set model to evaluation mode
    # I.e., turn off dropout and set batchnorm to use overall mean and variance (from training), rather than batch level mean and variance
    # Reference: https://github.com/pytorch/pytorch/issues/5406
    model.eval()
    losses = utils.AverageMeter()
    jaccards = utils.AverageMeter()
    
    # Turns off gradient calculations (https://datascience.stackexchange.com/questions/32651/what-is-the-use-of-torch-no-grad-in-pytorch)
    with torch.no_grad():
        tk0 = tqdm(data_loader, total=len(data_loader))
        # Make predictions and calculate loss / jaccard score for each batch
        for bi, d in enumerate(tk0):
            ids = d["ids"]
            token_type_ids = d["token_type_ids"]
            mask = d["mask"]
            sentiment = d["sentiment"]
            orig_selected = d["orig_selected"]
            orig_tweet = d["orig_tweet"][2]
            targets_start = d["targets_start"]
            targets_end = d["targets_end"]
            offsets = d["offsets"].numpy()
            targets_class = d["targets_class"]
            error_index = d["error_index"]

            # Move tensors to GPU for faster matrix calculations
            ids = ids.to(device, dtype=torch.long)
            token_type_ids = token_type_ids.to(device, dtype=torch.long)
            mask = mask.to(device, dtype=torch.long)
            targets_start = targets_start.to(device, dtype=torch.long)
            targets_end = targets_end.to(device, dtype=torch.long)
            targets_class = targets_class.to(device, dtype=torch.long)
            error_index = error_index.to(device, dtype=torch.long)

            # Predict logits for start and end indexes
            outputs_start, outputs_end, outputs_class = model(
                ids=ids,
                mask=mask,
                token_type_ids=token_type_ids,
                error_index=error_index
            )
            # Calculate loss for the batch
            loss = loss_fn(outputs_start, outputs_end, outputs_class, targets_start, targets_end, targets_class)
            # Apply softmax to the predicted logits for the start and end indexes
            # This converts the "logits" to "probability-like" scores
            outputs_start = torch.softmax(outputs_start, dim=1).cpu().detach().numpy()
            outputs_end = torch.softmax(outputs_end, dim=1).cpu().detach().numpy()
            outputs_class = [torch.softmax(i, dim=1).cpu().detach().numpy() for i in outputs_class]
            
            # Calculate jaccard scores for each tweet in the batch
            jaccard_scores = []
            for px, tweet in enumerate(orig_tweet):
                selected_tweet = orig_selected[px]
                tweet_sentiment = sentiment[px]
                ont_hot_class = [np.argmax(i[px, :]) for i in outputs_class]
                class_number = ont_hot_class.index(max(ont_hot_class))
                
                jaccard_score, _ = calculate_jaccard_score(
                    original_tweet=tweet,
                    target_string=selected_tweet,
                    sentiment_val=tweet_sentiment,
                    idx_start=np.argmax(outputs_start[px, :]),
                    idx_end=np.argmax(outputs_end[px, :]),
                    offsets=offsets[px],
                    class_number=class_number
                )
                jaccard_scores.append(jaccard_score)

            # Update running jaccard score and loss
            jaccards.update(np.mean(jaccard_scores), ids.size(0))
            losses.update(loss.item(), ids.size(0))
            # Print the running average loss and jaccard score
            tk0.set_postfix(loss=losses.avg, jaccard=jaccards.avg)
    
    print(f"Jaccard = {jaccards.avg}")
    return jaccards.avg

def calculate_jaccard_score(
    original_tweet, 
    target_string, 
    sentiment_val, 
    idx_start, 
    idx_end, 
    offsets,
    class_number,
    verbose=False):
    """
    Calculate the jaccard score from the predicted span and the actual span for a batch of tweets
    """
    # A span's end index has to be greater than or equal to the start index
    # If this doesn't hold, the start index is set to equal the end index (the span is a single token)
    if idx_end < idx_start:
        idx_end = idx_start
    
    # Combine into a string the tokens that belong to the predicted span
    filtered_output  = ""
    for ix in range(idx_start, idx_end + 1):
        filtered_output += original_tweet[offsets[ix][0]: offsets[ix][1]]
        # If the token is not the last token in the tweet, and the ending offset of the current token is less
        # than the beginning offset of the following token, add a space.
        # Basically, add a space when the next token (word piece) corresponds to a new word
        if (ix+1) < len(offsets) and offsets[ix][1] < offsets[ix+1][0]:
            filtered_output += " "
    #print(filtered_output)
    # Set the predicted output as the original tweet when the tweet's sentiment is "neutral", or the tweet only contains one word
    if sentiment_val == 0 or len(original_tweet.split()) < 2:
        filtered_output = original_tweet
    # Calculate the jaccard score between the predicted span, and the actual span
    # The IOU (intersection over union) approach is detailed in the utils module's `jaccard` function:
    # https://www.kaggle.com/abhishek/utils
    
    jac = utils.jaccard(target_string.strip(), filtered_output.strip())
    if class_number != sentiment_val:
        jac *= 0.5
    else:  
        if sentiment_val == 0:
            jac = 1
        
    return jac, filtered_output
