import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { range } from 'rxjs';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-documents',
  templateUrl: './documents-error.component.html',
  styleUrls: ['./documents-error.component.css']
})
export class DocumentsErrorComponent implements OnInit {
  public textForm = new FormGroup(
    { code: new FormControl(''), name: new FormControl(''), text: new FormControl('') }
  );

  constructor(public api: ApiService, private route: ActivatedRoute, private router: Router) {
  }
  Update() {
    this.api.getErrorCodeList().subscribe((responseBody) => {
      this.errors = responseBody['list'];
    });
  }
  onSubmit() {
    this.api.addErrorCode(this.textForm.value['code'], this.textForm.value['name'], this.textForm.value['text']).subscribe((responseBody) => {
      this.Update();
    }, (response)=>{
      var responseBody = response.error;
      alert(responseBody.error);
    });
  }

  errors = [];
  ngOnInit(): void {
    this.Update();
  }
}
