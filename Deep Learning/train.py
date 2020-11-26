import os
import torch
import pandas as pd
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
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

if __name__ == '__main__':
    if not os.path.isfile(config.BERT_PATH + "pytorch_model.bin"):
        print("사전 학습 모델 다운로드중")
        request.urlretrieve("https://share.easylab.kr/pytorch_model.bin",config.BERT_PATH + "pytorch_model.bin")
    print("사전 학습 모델 다운로드 완료")

    api = APIDokdo(config.API_KEY)
    original_data_json = api.getTrainingData()
    print("불러온 문서의 개수: ", len(original_data_json))

    for i in api.getErrorTypes():
        class_list_from_code[i['code']] = len(class_list)
        class_list.append(i['code'])

    original_data = []
    for i in original_data_json:
        d = split_document(i['contents'], i['errors'])
        original_data.extend(d)

    random.seed(0)
    random.shuffle(original_data)
    index = int(len(original_data) * 1)
    train = original_data[0:index]
    test_data = original_data[index:]
    test_data = original_data[0:index]
    # train dataset의 content를 반전시켜 노이즈를 추가
    length = len(train)
    for i in range(0,length):
        temp = [[train[i][0][j] for j in range(4,-1,-1)], train[i][1], train[i][2], train[i][3], train[i][4], train[i][5]]
        train.append(temp)

    training_data = train
    value_counts = [0] * len(class_list)
    for i in training_data:
        value_counts[i[1]] += 1

    print("class 비중 :", value_counts)
    def class_weight_set(train):
        training_data = []
        for i in train:
            training_data.append(i)
        temp = [] * len(class_list)
        for i in class_list:
            temp.append([])
        value_counts = [0] * len(class_list)
        for i in training_data:
            temp[i[1]].append(i)
            value_counts[i[1]] += 1

        vv = max(value_counts)
        print(vv)
        for i in range(0,len(class_list)):
            if len(temp[i]) == 0:
                continue
            for j in range(len(temp[i]), vv, len(temp[i])):
                training_data.extend(temp[i])

        return training_data

    training_data = class_weight_set(training_data)
    value_counts = [0] * len(class_list)
    for i in training_data:
        value_counts[i[1]] += 1

    print("class 비중(업데이트) :", value_counts)

    train_dataset = TextDataset(training_data)
    # Instantiate DataLoader with `train_dataset`
    # This is a generator that yields the dataset in batches
    train_data_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=config.TRAIN_BATCH_SIZE,
        num_workers=0,
        shuffle = True
    )
    #    shuffle = True
    valid_dataset = TextDataset(test_data)

    # Instantiate DataLoader with `train_dataset`
    # This is a generator that yields the dataset in batches
    valid_data_loader = torch.utils.data.DataLoader(
        valid_dataset,
        batch_size=config.TRAIN_BATCH_SIZE,
        num_workers=0,
        shuffle = True
    )
    # Set device as `cuda` (GPU)
    device = torch.device("cuda")
    # Load pretrained BERT (bert-base-uncased)
    model_config = transformers.BertConfig.from_pretrained(config.BERT_PATH)
    # Output hidden states
    # This is important to set since we want to concatenate the hidden states from the last 2 BERT layers
    model_config.output_hidden_states = True
    # Instantiate our model with `model_config`
    model = TweetModel(conf=model_config, num_labels=len(class_list))
    # Move the model to the GPU
    model.to(device)

    # Calculate the number of training steps
    num_train_steps = int(len(training_data) / config.TRAIN_BATCH_SIZE * config.EPOCHS)
    # Get the list of named parameters
    param_optimizer = list(model.named_parameters())
    # Specify parameters where weight decay shouldn't be applied
    no_decay = ["bias", "LayerNorm.bias", "LayerNorm.weight"]
    # Define two sets of parameters: those with weight decay, and those without
    optimizer_parameters = [
        {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)], 'weight_decay': 0.001},
        {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)], 'weight_decay': 0.0},
    ]
    # Instantiate AdamW optimizer with our two sets of parameters, and a learning rate of 3e-5
    optimizer = AdamW(optimizer_parameters, lr=3e-5)
    # Create a scheduler to set the learning rate at each training step
    # "Create a schedule with a learning rate that decreases linearly after linearly increasing during a warmup period." (https://pytorch.org/docs/stable/optim.html)
    # Since num_warmup_steps = 0, the learning rate starts at 3e-5, and then linearly decreases at each training step
    scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=0, 
        num_training_steps=num_train_steps
    )

    # Apply early stopping with patience of 2
    # This means to stop training new epochs when 2 rounds have passed without any improvement
    es = utils.EarlyStopping(patience=2, mode="max")
    fold = 0
    print(f"Training is Starting for fold={fold}")

    # I'm training only for 3 epochs even though I specified 5!!!
    for epoch in range(50):
        train_fn(train_data_loader, model, optimizer, device, scheduler=scheduler)
        jaccard = eval_fn(valid_data_loader, model, device)
        print(f"Jaccard Score = {jaccard}")
        es(jaccard, model, model_path=f"model_{fold}.bin")
        if es.early_stop:
            print("Early stopping")
            break
            
    del model