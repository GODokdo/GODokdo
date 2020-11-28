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
from PIL import Image
from io import BytesIO
import pytesseract
capabilities = {
  'browserName': 'chrome',
  'chromeOptions':  {
    'useAutomationExtension': False,
    'args': ['--disable-infobars']
  }
}
from urllib.parse import urlparse
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from urllib.parse import quote_plus
import time
import json
import base64
driver = webdriver.Chrome(executable_path='chromedriver')
def web_read(url):
    driver.get(url)
    time.sleep(3)
    soup = bs(driver.find_element_by_xpath("//*").get_attribute("outerHTML"))
    script_tag = soup.find_all(['script', 'style', 'header', 'footer', 'form','nav'])

    for script in script_tag:
        script.extract()
    content = soup.get_text('\n', strip=True)
    html_title = None
    try:
        html_title = soup.find('title').string.strip()
    except:
        print("타이틀 없음")
    obj = urlparse(url)
    domain = obj.netloc
    if html_title is not None:
        title = domain + " - " + html_title
    else:
        title = url
    image = chrome_takeFullScreenshot()
    return {'title':title, 'contents': content, 'image': image }

def chrome_takeFullScreenshot():
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
        print("image_ocr", document_no, "번 문서 열람")
        if 'file' in document and document['file'] is not None:
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

def url_web():
    for document in getDocuments(status='registered'):
        document_no = document['document']['no']
        print("url_web", document_no, "번 문서 열람")
        if document['document']['url'] != None:
            data = web_read(document['document']['url'])
            p = '../upload/' + str(document_no)
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'wb') as f:
                f.write(data['image'])
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
while True:
    image_ocr()
    text_ai()
    url_web()
    time.sleep(1)