import { Component, ElementRef, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { ApiService } from '../../api.service';

@Component({
  selector: 'document-view',
  templateUrl: './document-view.component.html',
  styleUrls: ['./document-view.component.scss']
})
export class DocumentViewComponent implements OnInit {
  errorForm = new FormGroup(
    { text: new FormControl(''), code: new FormControl(0) }
  );

  @ViewChild('primaryModal') public primaryModal: ModalDirective;
  private no: number;
  constructor(route: ActivatedRoute, public api: ApiService, private elRef: ElementRef) {
    this.no = route.snapshot.params['no'];

  }
  isCollapsed: boolean = false;
  selectText() {
    var selectionText;
    if (document.getSelection) {
      selectionText = document.getSelection();
    }
    return selectionText;
  }
  getStatusLevel() {
    if (this.result.document.status == "registered") return 1;
    if (this.result.document.status == "collected") return 2;
    if (this.result.document.status == "labeled") return 3;
    if (this.result.document.status == "verified") return 5;
  }
  errorSubmit() {
    var code = this.errorForm.controls.code.value;
    var text = this.errorForm.controls.text.value;
    this.api.addDocumentError(this.no, code, text).subscribe((responseBody) => {
      this.primaryModal.hide();
      this.Update();
    }, (response) => {
      var responseBody = response.error;
      alert(responseBody.error);
    });
  }
  addError(error_text) {
    this.errorForm.controls.code.setValue(0);
    this.errorForm.controls.text.setValue(error_text);

    this.api.getErrorCodeList().subscribe((responseBody) => {
      this.error_codes = responseBody['list'];
    });

    this.primaryModal.show();
  }

  selected_span = null;
  public result = null;
  public error_codes = [];
  public contents = [];
  public tryed = false;
  Update() {
    if (this.tryed) return;
    this.tryed = true;
    this.api.getDocumentFromNo(this.no).subscribe((responseBody) => {
      this.result = responseBody;
      if (this.result.document.contents != null) {
        this.contents = [{ 'tag': 'text', 'text': this.result.document.contents }];
        var errors = this.result.errors;
        for (var i in errors) {
          var keyword = errors[i]['text'];
          for (var j in this.contents) { // temp 수정시 다시 처음부터 작동함
            if (this.contents[j]['tag'] == 'text') {
              var position = this.contents[j]['text'].indexOf(keyword);
              console.log(this.contents[j]['text'])
              console.log(keyword)
              if (position == -1) continue;
              var before = { 'tag': 'text', 'text': this.contents[j]['text'].substring(0, position) };
              var now = { 'tag': 'error', 'error': errors[i], 'text': this.contents[j]['text'].substring(position, position + keyword.length) };
              var after = { 'tag': 'text', 'text': this.contents[j]['text'].substring(position + keyword.length) };

              this.contents.splice(Number(j), 1, before, now, after)

            }
          }
        }
      }
    }, (error) => { }, () => {
      this.tryed = false;
    });
  }
  timeForToday(value) {
    const today = new Date();
    const timeValue = new Date(value);

    const betweenTime = Math.floor((today.getTime() - timeValue.getTime()) / 1000 / 60);
    if (betweenTime < 1) return '방금 전';
    if (betweenTime < 60) {
      return `${betweenTime}분 전`;
    }

    const betweenTimeHour = Math.floor(betweenTime / 60);
    if (betweenTimeHour < 24) {
      return `${betweenTimeHour}시간 전`;
    }

    const betweenTimeDay = Math.floor(betweenTime / 60 / 24);
    if (betweenTimeDay < 365) {
      return `${betweenTimeDay}일 전`;
    }

    return `${Math.floor(betweenTimeDay / 365)}년 전`;
  }

  updated_time = null;
  ngOnInit(): void {
    this.Update();
    setInterval(() => {
      this.api.getDocumentStatus(this.no).subscribe((responseBody) => {
        if (this.updated_time != responseBody['updated_time']) {
          this.updated_time = responseBody['updated_time'];
          this.Update();
        }
      });
    }, 1000);
    document.onmouseup = () => {
      var created = null;
      var select = this.selectText();
      if (select.focusNode != null &&
        select.focusNode.parentElement.classList.contains("text")
        && select.toString().length != 0) {
        if (select.rangeCount) {
          var range = document.createRange();
          range.setStart(select.anchorNode, select.anchorOffset);
          range.setEnd(select.focusNode, select.focusOffset);
          var backwards = range.collapsed;
          range.detach();

          // modify() works on the focus of the selection
          var endNode = select.focusNode, endOffset = select.focusOffset;
          select.collapse(select.anchorNode, select.anchorOffset);

          var direction = [];
          if (backwards) {
            direction = ['backward', 'forward'];
          } else {
            direction = ['forward', 'backward'];
          }

          select.modify("move", direction[0], "character");
          select.modify("move", direction[1], "word");
          select.extend(endNode, endOffset);
          select.modify("extend", direction[1], "character");
          select.modify("extend", direction[0], "word");
          console.log(select.toString())

          var wrapper = document.createElement('div');
          wrapper.innerHTML = document.getElementsByClassName("selected")[0].outerHTML;
          created = wrapper.firstChild;
          range = select.getRangeAt(0).cloneRange();
          range.surroundContents(created);
          select.removeAllRanges();
          select.addRange(range);
        }
      }

      if (this.selected_span != null) {
        if (select.focusNode.parentElement.classList.contains("text")) {
          this.selected_span.outerHTML = this.selected_span.innerHTML;
          this.selected_span = null;
        }
      }
      if (created != null) {
        this.selected_span = created;
        let elementList = this.elRef.nativeElement.querySelectorAll('span.selected');
        elementList[1].addEventListener('click', this.addError.bind(this, created.innerText));
        document.getSelection().empty();
      }
    }
  }
}
