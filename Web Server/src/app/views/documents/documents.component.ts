import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.component.html',
  styleUrls: ['./documents.component.css']
})
export class DocumentsComponent implements OnInit {

  constructor(public api: ApiService) { }
  public documents = [];
  ngOnInit(): void {
    this.api.getDocumentList().subscribe((responseBody) => {
      this.documents = responseBody['list'];
  });

  }

}
