import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { range } from 'rxjs';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.component.html',
  styleUrls: ['./documents.component.css']
})
export class DocumentsComponent implements OnInit {

  public documents = [];
  public pages = [];
  public limit: number = 10;
  public limit_pages: number = 10;
  public page_no: number = 1;
  public prev_no = 1;
  public next_no = 1;
  constructor(public api: ApiService, private route: ActivatedRoute) { 
    this.route.queryParams.subscribe(params => {
      if (params['page'] != null)
        this.page_no = params['page'];
      else
        this.page_no = 1;
      this.Update();
  });
  }

  Update() {
    this.api.getDocumentList(this.limit, this.page_no).subscribe((responseBody) => {
        this.pages = []
        this.documents = responseBody['list'];
        var count = responseBody['count'];
    
        var max_page = parseInt(String((count - 1) / this.limit + 1), 0);
        var start_page = parseInt(String((this.page_no - 1) / this.limit_pages), 0) * this.limit_pages + 1;
        range(start_page, this.limit_pages).forEach(element => {
          if (element <= max_page) 
            this.pages.push(element);
        });
        this.next_no = start_page + this.limit_pages;
        if (this.next_no > max_page) this.next_no = max_page;
        
        this.prev_no = start_page - 1;
        if (this.prev_no < 1) this.prev_no = 1;
        console.log(this.next_no);
    });
  }
  ngOnInit(): void {

  }

}
