import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export const API_URL = "https://api.easylab.kr"
const authorization = "godapikey12"

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private httpClient: HttpClient) { }
  getErrorCodeList() {
    return this.httpClient.get("https://api.easylab.kr/error", { 'headers': { 'authorization': authorization } });
  }

  addDocumentError(no, code,sentence_no, position, length, text) {
    return this.httpClient.post("https://api.easylab.kr/document/" + no + "/error", { "sentence_no":sentence_no, "code": code, "position": position, "length":length, "text":text }, { 'headers': { 'authorization': authorization } });
  }

  getDocumentList() {
    return this.httpClient.get("https://api.easylab.kr/document", { 'headers': { 'authorization': authorization } });
  }

  getDocumentFromNo(no, content_type="string") {
    return this.httpClient.get("https://api.easylab.kr/document/" + no, { 'headers': { 'authorization': authorization }, 'params':{'content-type':content_type} });
  }

  getDocumentStatus(no) {
    return this.httpClient.get("https://api.easylab.kr/document/" + no + "/status", { 'headers': { 'authorization': authorization } });
  }

  addDocumentFromText(title, contents) {
    return this.httpClient.post("https://api.easylab.kr/document", { "title": title, "contents": contents }, { 'headers': { 'authorization': authorization } });
  }

  modifyDocumentFromText(no, status) {
    return this.httpClient.put("https://api.easylab.kr/document/" + no, { "status": status}, { 'headers': { 'authorization': authorization } });
  }

  translate(text, src = "", dest = "") {
    return this.httpClient.get("https://api.easylab.kr/translate/from/google", { 'headers': { 'authorization': authorization }, 'params':{'src':src, 'dest': src, 'text':text}});
  }
}
