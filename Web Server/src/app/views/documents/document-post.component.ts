import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-documents',
  templateUrl: './document-post.component.html',
  styleUrls: ['./document-post.component.css']
})
export class DocumentPostComponent implements OnInit {

  textForm = new FormGroup(
    { title: new FormControl(''), contents: new FormControl('') }
  );

  constructor(public api: ApiService, private router: Router) { }
  ngOnInit(): void {
  }
  onSubmit() {    
    var title = this.textForm.controls.title.value;
    var contents = this.textForm.controls.contents.value;
    console.log(title);

    this.api.addDocumentFromText(title, contents).subscribe((responseBody) => {
      
      this.router.navigateByUrl('/documents/view/' + responseBody['created_document_no']);
    }, (response) => {
      var responseBody = response.error;
      alert(responseBody.error);
    });


  }

}
