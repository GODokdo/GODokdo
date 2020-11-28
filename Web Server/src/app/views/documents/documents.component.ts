import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
  public error_codes = [];
  public error_code_index = {};
  public count = 0;
  public searchForm = new FormGroup(
    { status: new FormControl(''), error: new FormControl(''), crawling: new FormControl('') }
  );

  constructor(public api: ApiService, private route: ActivatedRoute, private router: Router) {
    this.route.queryParams.subscribe(params => {
      if (params['page'] != null)
        this.page_no = params['page'];
      else
        this.page_no = 1;

      this.searchForm.setValue({
        'status': params['status'] ? params['status'] : "",
        'error': params['error'] ? params['error'] : "",
        'crawling': params['crawling'] ? params['crawling'] : ""
      })
      this.Update();
    });
  }
  onSubmit() {
    this.pageMove(1);
  }
  pageMove(no) {
    this.router.navigate(['/documents/list'], {
      queryParams: {
        'page': no,
        'status': this.searchForm.value['status'],
        'error': this.searchForm.value['error'],
        'crawling': this.searchForm.value['crawling']
      }
    })
  }
  Update() {
    this.api.getDocumentList(this.limit, this.page_no, this.searchForm.value['status'], this.searchForm.value['error'], this.searchForm.value['crawling']).subscribe((responseBody) => {
      this.pages = []
      this.documents = responseBody['list'];

      this.documents.forEach(document => {
        var error_arr = {}
        document.distinct_errors = []
        document.errors.forEach(element => {
          if (error_arr[element] == null)
          {
            error_arr[element] = 1
            document.distinct_errors.push(element)
          }
        });
      });

      this.count = responseBody['count'];

      var max_page = parseInt(String((this.count - 1) / this.limit + 1), 0);
      var start_page = parseInt(String((this.page_no - 1) / this.limit_pages), 0) * this.limit_pages + 1;
      range(start_page, this.limit_pages).forEach(element => {
        if (element <= max_page)
          this.pages.push(element);
      });
      this.next_no = start_page + this.limit_pages;
      if (this.next_no > max_page) this.next_no = max_page;

      this.prev_no = start_page - 1;
      if (this.prev_no < 1) this.prev_no = 1;
    });
  }

  ngOnInit(): void {
    this.api.getErrorCodeList().subscribe((responseBody) => {
      this.error_codes = responseBody['list'];
      this.error_codes.forEach(element => {
        this.error_code_index[element['code']] = element['name'];
      });
    });

  }
}
