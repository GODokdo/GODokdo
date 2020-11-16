import requests
import csv
import re
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from urllib.parse import quote_plus
import json, base64
import datetime

class APIDokdo:
    def __init__(self, apikey):
      self.apiurl = "https://api.easylab.kr"
      self.headers =  {'authorization': apikey}
    def addDocument(self, url=None, title=None, contents=None):
       return requests.post(
          self.apiurl + "/document",
          data={'url':url, 'title':title, 'contents':contents}, 
          headers=self.headers
        )

    def getDocument(self, status=None):
        return requests.get(self.apiurl + "/document",params={'status':status}, headers=self.headers).json()['list']

    def updateDocument(self, document_no, status, title = None, contents=None):
       return requests.put(
          self.apiurl + "/document/" + str(document_no),
          data={'status':status, 'title':title, 'contents':contents}, 
          headers=self.headers
        )
    def AddDocument(self, URL):      
        return requests.post(
          self.apiurl + "/document/",
          data={'status':status, 'url':title, 'contents':contents}, 
          headers=self.headers
        )



# API 객체 생성 + API 키 입력
api = APIDokdo("godapikey12")

# 서버에는 고유한 URL을 기반으로 생성된 Document라는 객체가 있음. 
# 4가지 Status
# - registered: URL 링크만 등록된 상태(크롤링에 의해 URL이 등록되었을 수도 있고, 사용자가 웹페이지 분석을 요청한 경우일 수도 있음 ) -> 본문을 스크랩해야함
# - collected: 본문이 채워져있는 상태. -> 머신러닝을 작동시켜서 라벨을 추가해야함.
# - labeled: 인공지능을 통해 표기 오류가 검출되어있는 문서 -> 사람이 직접 확인해야함
# - verified: 사람이 표기 오류 검증을 끝낸 상태 -> 자동으로 학습 데이터에 활용됨


# 새로운 문서 등록
# api.addDocument(url="https://naver.com/1", title="타이틀", contents="본문") # 제목과 내용이 있으니 registered 상태를 건너뜀

temp_url = "https://naver.com/" + str(datetime.datetime.now()) + "/문서 등록해서 내용 업데이트 테스트"
temp_url2 = "https://naver.com/" + str(datetime.datetime.now()) + "/문서 URL만 등록"

result = api.addDocument(url=temp_url) # 제목과 내용이 없으니 registered 상태가 됨.
if result.status_code == 201:
  print("새로운 URL 등록 성공")
  print("    문서 고유 URL", result.json()["created_document_url"])

  print("")
  
  # 이제 URL이 등록된 문서를 가져와서 본문을 채우는 작업을 수행해야함.
  # registered 상태의 문서만 가져오기
  document_list = api.getDocument(status='registered')
  print("URL만 등록된 문서의 개수:", len(document_list))
  for document in document_list:
    document_no = document['no']
    document_url = document['url']
    print(document)
    # 여기에 스크랩 코드... 
    title = "웹사이트 제목"
    contents = "웹사이트 내용"
    result = api.updateDocument(document_no, status="collected", title=title, contents=contents)
    if result.status_code == 201:
      print("업데이트 성공")
    else:
      print("업데이트 실패:" + result.json()['error'])

else:
  print("새로운 URL 등록 실패. 이유:", result.json()['error'])



# 만약 문서 내용을 초기화시키고싶다면 아래의 코드 입력
document_no = 320
result = api.updateDocument(document_no, status="registered")
if result.status_code == 201:
  print(document_no, "번 문서 초기화 성공")
else:
  print(document_no, "번 문서 초기화 실패. 이유:", result.json()['error'])



result = api.addDocument(url=temp_url2) # 제목과 내용이 없으니 registered 상태가 됨.
if result.status_code == 201:
  print("새로운 URL 등록 성공")
  print("    문서 고유 URL", result.json()["created_document_url"])

  print("")