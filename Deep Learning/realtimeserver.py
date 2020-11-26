import os
import torch
import pandas as pd
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
import time
from torch.optim import lr_scheduler

from sklearn import model_selection
from sklearn import metrics
import transformers
import tokenizers
from transformers import AdamW
from transformers import get_linear_schedule_with_warmup
from tqdm.autonotebook import tqdm
import utils
import random
from config import *
from value import *
from api import *
from preprocessing import *
from dataloader import *
from model import *

api = APIDokdo(config.API_KEY)
original_data_json = api.getTrainingData()
print("불러온 문서의 개수: ", len(original_data_json))

for i in api.getErrorTypes():
    class_list_from_code[i['code']] = len(class_list)
    class_list.append(i['code'])

device = torch.device("cpu")
model_config = transformers.BertConfig.from_pretrained(config.BERT_PATH)
model_config.output_hidden_states = True

model1 = TweetModel(conf=model_config, num_labels=len(class_list))
model1.to(device)
model1.load_state_dict(torch.load("model_0.bin"))
model1.eval()

while True:
    documents =  api.getDocumentList(status='collected')
    for item in documents:
        document_no = item['no']
        document = api.getDocument(document_no)
        
        print(document_no, "번 문서 열람")
        sentences = split_document(document['document']['contents'], [])
        for sentence in sentences:
            sentence_no = getInformationFromSentence(sentence)['sentence_no'] - 2 # padding
            main_text = getInformationFromSentence(sentence)['text'][2]
            while True:
                sentence[0][2] = main_text
                newdataset = TextDataset([sentence])
                d = newdataset[0]
                with torch.no_grad():
                    ids = d["ids"]
                    token_type_ids = d["token_type_ids"]
                    mask = d["mask"]
                    sentiment = d["sentiment"]
                    orig_selected = d["orig_selected"]
                    orig_tweet = d["orig_tweet"][2]
                    targets_start = d["targets_start"]
                    targets_end = d["targets_end"]
                    offsets = d["offsets"].numpy()
                    error_index = d["error_index"]

                    ids = ids.to(device, dtype=torch.long).view(1,-1)
                    token_type_ids = token_type_ids.to(device, dtype=torch.long).view(1,-1)
                    mask = mask.to(device, dtype=torch.long).view(1,-1)
                    error_index = error_index.to(device, dtype=torch.long).view(1,-1)
                    # Predict start and end logits for each of the five models
                    outputs_start, outputs_end, outputs_class = model1(
                        ids=ids,
                        mask=mask,
                        token_type_ids=token_type_ids,
                        error_index=error_index
                    )
                    outputs_start = torch.softmax(outputs_start, dim=1).cpu().detach().numpy()
                    outputs_end = torch.softmax(outputs_end, dim=1).cpu().detach().numpy()
                    outputs_class = [torch.softmax(i, dim=1).cpu().detach().numpy() for i in outputs_class]
                    ont_hot_class = [np.argmax(i) for i in outputs_class]
                    class_number = ont_hot_class.index(max(ont_hot_class))

                    _, output_sentence = calculate_jaccard_score(
                    original_tweet=orig_tweet,
                    target_string="new keyword",
                    sentiment_val=999999,
                    idx_start=np.argmax(outputs_start),
                    idx_end=np.argmax(outputs_end),
                    offsets=offsets,
                    class_number = class_number)
                    if (class_number != 0):
                        output_sentence = output_sentence.strip()
                        position = main_text.find(output_sentence)
                        length = len(output_sentence)
                        print("Detected")
                        if (position == -1 or length == 0): break
                        print(getInformationFromSentence(sentence)['sentence_no'], class_number, output_sentence)
                        result = api.AddDocumentError(document_no, sentence_no, class_list[class_number], position, length, output_sentence)  
                        print(result.json())
                        main_text = main_text[:position] + (' ' * length) + main_text[position+length:]
                    else:
                        break
        api.updateDocument(document_no, 'labeled')
    time.sleep(1)