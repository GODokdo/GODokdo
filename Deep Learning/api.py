import requests
class APIDokdo:
    def __init__(self, apikey):
      self.apiurl = "https://api.easylab.kr"
      self.headers =  {'authorization': apikey}
    def getTrainingData(self):
        return requests.get(self.apiurl + "/deeplearning/data/sentences", headers=self.headers).json()['list']
    def getErrorTypes(self):
        return requests.get(self.apiurl + "/error", headers=self.headers).json()['list']
    def getDocumentList(self, status=None):
        return requests.get(self.apiurl + "/document",params={'status':status}, headers=self.headers).json()['list']
    def getDocument(self, no=None):
        return requests.get(self.apiurl + "/document/" + str(no), headers=self.headers).json()
    def AddDocumentError(self, document_no, sentence_no, code, position, length, text):      
        return requests.post(
          self.apiurl + "/document/" + str(document_no) + "/error",
          data={'sentence_no':sentence_no, 'text':text, 'code':code, 'position':position, 'length':length}, 
          headers=self.headers
        )
    def updateDocument(self, document_no, status, title = None, contents=None):
        return requests.put(
          self.apiurl + "/document/" + str(document_no),
          data={'status':status, 'title':title, 'contents':contents}, 
          headers=self.headers
        )