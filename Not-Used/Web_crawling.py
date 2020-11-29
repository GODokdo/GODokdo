import requests
import csv
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from urllib.parse import quote_plus
import json, base64
import re
import trafilatura




capabilities = {
  'browserName': 'chrome',
  'chromeOptions':  {
    'useAutomationExtension': False,
    'args': ['--disable-infobars']
  }
}


def web_crawler(url, path):
    print(url)
    driver = webdriver.Chrome(executable_path='/Users/kimjihyeon/Desktop/chromedriver')
    driver.get(url)

    html = driver.page_source
    soup = bs(html, "html.parser")
    search_list = []
    print('== URLs ==')
    
    r = soup.find_all('a')
    search_list.append(url) # 현재 url도 추가
        
    links = soup.find_all(name="a", href=re.compile("https://") )

    for i in links:
        hyperlink = i.get('href')
        if(hyperlink[0]=='h'):
            print(i.get('href'),'\n')
            search_list.append(i.get('href'))
    
    num =0
    for i in range(1):
        print(num)
        png = chrome_takeFullScreenshot(search_list[i])
        p = path+'/screen'+str(i)+'.png'
        with open(p, 'wb') as f:
            f.write(png)
        num=num+1
        
    content_extract_without_t(search_list)

def content_extract_with_t(url_list):
    # 포문 돌면서 리스트 하나씩 꺼내서 아래 내용 돌면서 본문 출력함
    
    for i in range(len(url_list)):
        print('URL :',url_list[i])
        downloaded = trafilatura.fetch_url(url_list[i])
        content = trafilatura.extract(downloaded)

        
        print("*************************************************************************************************")
        print(content)
        print("*************************************************************************************************")

def content_extract_without_t(url_list):
    # 포문 돌면서 리스트 하나씩 꺼내서 아래 내용 돌면서 본문 출력함    
    for i in range(len(url_list)):
        url = url_list[i]
        html = requests.get(url)
        soup = bs(html.text)
        script_tag = soup.find_all(['script', 'style', 'header', 'footer', 'form','nav','a'])

        for script in script_tag:
            script.extract()
            content = soup.get_text('\n', strip=True)

        print('url: ',url_list[i])
        print("*************************************************************************************************")
        print(content)
        print("*************************************************************************************************")
        

def chrome_takeFullScreenshot(url) :
  driver = webdriver.Chrome(executable_path='/Users/kimjihyeon/Desktop/chromedriver')
  driver.get(url)
    
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


url = input('Url 을 입력하세요: ')
path = input('Screen shot 을 저장할 경로를 입력하세요: ')
web_crawler(url,path)

