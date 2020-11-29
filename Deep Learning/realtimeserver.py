import os
import torch
import pandas as pd
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
import time
import re
import traceback
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
from PIL import Image
from io import BytesIO
import pytesseract

from urllib.parse import urlparse
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from urllib.parse import quote_plus
import time
import json
import base64
import threading

def getdomain(url):
    obj = urlparse(url)
    domain = obj.netloc
    return domain

def web_read(driver, url):
    driver.get(url)
    time.sleep(3)
    try:
        soup = bs(driver.page_source)
    except:
        return {'title':url, 'contents': '일반적인 웹페이지 형식이 아님', 'image': None}
    
    script_tag = soup.find_all(['script', 'style', 'header', 'footer', 'form','nav'])

    for script in script_tag:
        script.extract()
    content = soup.get_text('\n', strip=True)
    html_title = None
    try:
        html_title = soup.find('title').string.strip()
    except:
        print("타이틀 없음")
    if html_title is not None:
        title = getdomain(url) + " - " + html_title
    else:
        title = url
    image = chrome_takeFullScreenshot(driver)
    return {'title':title, 'contents': content, 'image': image }

def chrome_takeFullScreenshot(driver):
    def send(cmd, params):
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd':cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def evaluate(script):
        response = send('Runtime.evaluate', {'returnByValue': True, 'expression': script})
        return response['result']['value']

    metrics = evaluate( \
    "({" + \
        "width: Math.max(window.innerWidth, document.body.scrollWidth, document.documentElement.scrollWidth)|0," + \
        "height: Math.max(innerHeight, document.body.scrollHeight, document.documentElement.scrollHeight)|0," + \
        "deviceScaleFactor: window.devicePixelRatio || 1," + \
        "mobile: typeof window.orientation !== 'undefined'" + \
    "})")
    send('Emulation.setDeviceMetricsOverride', metrics)
    screenshot = send('Page.captureScreenshot', {'format': 'png', 'fromSurface': True})
    send('Emulation.clearDeviceMetricsOverride', {})
    if screenshot is None or 'data' not in screenshot:
        return None
    return base64.b64decode(screenshot['data'])
# print(web_read("https://www.britannica.com/place/Sea-of-Japan"))
# exit()

api = APIDokdo(config.API_KEY)
original_data_json = api.getTrainingData()
print("불러온 문서의 개수: ", len(original_data_json))

for i in api.getErrorTypes():
    class_list_from_code[i['code']] = len(class_list)
    class_list.append(i['code'])

device = torch.device("cuda")
model_config = transformers.BertConfig.from_pretrained(config.BERT_PATH)
model_config.output_hidden_states = True

model1 = TweetModel(conf=model_config, num_labels=len(class_list))
model1.to(device)
model1.load_state_dict(torch.load("model_0.bin"))
model1.eval()


def getDocuments(*args, **kwargs):
    result = []
    try:
        documents =  api.getDocumentList(*args, **kwargs)
    except:
        time.sleep(1)
        return []

    for item in documents:
        document_no = item['no']
        try:
            document = api.getDocument(document_no)
            result.append(document)
        except:
            time.sleep(1)
            continue

    return result

def image_ocr():
    for document in getDocuments(status='registered'):
        document_no = document['document']['no']
        if 'file' in document and document['file'] is not None:
            print("image_ocr", document_no, "번 문서 열람")
            r = requests.get(document['file'], stream=True)
            try:
                if r.status_code == 200:
                    image = Image.open(BytesIO(r.content))
                    string = pytesseract.image_to_string(image, lang='eng')
                    image.close()
                if (len(string.strip()) == 0):
                    string = "Not Found"
                api.updateDocument(document_no, 'collected', title = document['document']['title'], contents=string)
            except:
                
                print(document_no, "번 문서에서 이미지 열기 오류")

def url_web(driver):
    for document in getDocuments(status='registered'):
        document_no = document['document']['no']
        print("url_web", document_no, "번 문서 열람")
        if document['document']['url'] != None:
            data = web_read(driver, document['document']['url'])
            p = '../upload/' + str(document_no)
            if data['image'] != None:
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'wb') as f:
                    f.write(data['image'])
            if (len(data['contents'].strip()) == 0):
                data['contents'] = "Not Found"
            api.updateDocument(document_no, 'collected', title = data['title'], contents=data['contents'])

def text_ai():
    for document in getDocuments(status='collected'):
        document_no = document['document']['no']
        print("text_ai", document_no, "번 문서 열람")
        if (document['document']['contents'] is None):
            continue
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

def thread_image_ocr():
    while True:
        image_ocr()
        time.sleep(1)

def thread_text_ai():
    while True:
        text_ai()
        time.sleep(1)

options = webdriver.ChromeOptions()
options.add_argument('mute-audio')
def thread_url_web():
    while True:
        try:
            driver = webdriver.Chrome(executable_path='chromedriver', options=options)
            while True:
                url_web(driver)
                time.sleep(1)
        except Exception as e:
            print("URL_WEB 에러 발생\n", e)
            traceback.print_stack()
            traceback.print_exc()

def thread_crawling():
    while True:
        try:
            driver = webdriver.Chrome(executable_path='chromedriver', options=options)
            while True:
                crawling(driver)
                time.sleep(11111)
        except Exception as e:
            print("크롤링 에러 발생\n", e)
            traceback.print_stack()
            traceback.print_exc()

visited = {}
def web_explorer(driver, URL, depth):
    if (depth < 0):
        return
    if (URL in visited):
        return
    if (getdomain(URL).find("google") != -1 and URL.find("/search") == -1):
        return
    if (getdomain(URL).find("cache") != -1):
        return
    
    print("크롤링", depth, URL)
    visited[URL] = depth
    driver.get(URL)
    time.sleep(10)

    try:
        soup = bs(driver.page_source)
    except:
        return

    # 현재 페이지 추가
    api.AddDocument(URL)
    links = soup.find_all(name="a", href=re.compile("https://") )

    for i in links:
        hyperlink = i.get('href')
        if(hyperlink[0]=='h'):
            web_explorer(driver, i.get('href'), depth - 1)
    
def crawling(driver):
    return
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=sea of japan&start=0", 2)
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=takeshima&start=0", 2)
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=sea of japan&start=0", 2)
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=Korea was a part of China&start=0", 2)
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=Hermit Kingdom&start=0", 2)
    web_explorer(driver, "https://www.google.com/search??hl=en&source=hp&q=Gutenberg&start=0", 2)
    return

threads = []
threads.append(threading.Thread(target=thread_image_ocr))
threads.append(threading.Thread(target=thread_text_ai))
threads.append(threading.Thread(target=thread_url_web))
threads.append(threading.Thread(target=thread_crawling))
for i in threads:
    i.start()


while True:
    time.sleep(1)