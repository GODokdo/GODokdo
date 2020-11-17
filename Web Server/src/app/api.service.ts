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

  addDocumentError(no, code, text) {
    return this.httpClient.post("https://api.easylab.kr/document/" + no + "/error", { "code": code, "text": text }, { 'headers': { 'authorization': authorization } });
  }

  getDocumentList() {
    return this.httpClient.get("https://api.easylab.kr/document", { 'headers': { 'authorization': authorization } });
  }

  getDocumentFromNo(no) {
    return this.httpClient.get("https://api.easylab.kr/document/" + no, { 'headers': { 'authorization': authorization } });
  }

  getDocumentStatus(no) {
    return this.httpClient.get("https://api.easylab.kr/document/" + no + "/status", { 'headers': { 'authorization': authorization } });
  }

  addDocumentFromText(title, contents) {
    return this.httpClient.post("https://api.easylab.kr/document", { "title": title, "contents": contents }, { 'headers': { 'authorization': authorization } });
  }
}
