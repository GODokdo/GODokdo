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
    { sentence_no: new FormControl(''), text: new FormControl(''), code: new FormControl(0), position: new FormControl(0), length: new FormControl(0) }
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
    var position = this.errorForm.controls.position.value;
    var length = this.errorForm.controls.length.value;
    var sentence_no = this.errorForm.controls.sentence_no.value;
    this.api.addDocumentError(this.no, code, sentence_no, position, length).subscribe((responseBody) => {
      this.primaryModal.hide();
      this.Update();
    }, (response) => {
      var responseBody = response.error;
      alert(responseBody.error);
    });
  }
  addError(sentence_no, error_text, position) {
    error_text = error_text.trim()
    this.errorForm.controls.sentence_no.setValue(sentence_no);
    this.errorForm.controls.code.setValue(0);
    this.errorForm.controls.text.setValue(error_text);
    this.errorForm.controls.position.setValue(position);
    this.errorForm.controls.length.setValue(error_text.length);

    this.api.getErrorCodeList().subscribe((responseBody) => {
      this.error_codes = responseBody['list'];
    });

    this.primaryModal.show();
  }

  selected_span = null;
  public result = null;
  public error_codes = [];
  public contents = [];
  public translate_contents = [];
  public tryed = false;
  public previous_contents = "";
  Update() {
    if (this.tryed) return;
    this.tryed = true;
    this.api.getDocumentFromNo(this.no, "array").subscribe((responseBody) => {
      this.updated_time = responseBody['document']['updated_time'];
      this.result = responseBody;
      if (this.previous_contents != String(this.result.document.contents))
      {
        this.previous_contents = String(this.result.document.contents);

        this.result.document.contents.forEach((sentence, index) => {
          this.api.translate(sentence).subscribe((responseBody) => {
            console.log(index)
            this.translate_contents[index] = responseBody['translated']
          });
        });
      }
      this.contents = []
      if (this.result.document.contents != null) {
        var errors = this.result.errors;
        errors = errors.sort(function (a, b): any {
            const dataA = a['position'];
            const dataB = b['position'];
            return dataB > dataA ? 1 : dataB < dataA ? -1 : 0; //sort by date decending
        });
        console.log(errors)
        for (var sentence_i in this.result.document.contents)
        {
          var sentence = this.result.document.contents[sentence_i]
          var tags = [{ 'offset':0, 'sentence_no': sentence_i, 'tag': 'text', 'text': sentence }];
          for (var i in errors) {
            if (errors[i]['sentence_no'] != sentence_i) continue
            for (var j in tags) { // temp 수정시 다시 처음부터 작동함
              if (tags[j]['tag'] == 'text') {
                // var position = tags[j]['text'].toLowerCase().indexOf(keyword.toLowerCase());
                var before = { 'offset': tags[j]['offset'], 'sentence_no': sentence_i, 'tag': 'text', 'text': tags[j]['text'].substring(0, errors[i]['position']) };
                var now = { 'offset': tags[j]['offset'] + errors[i]['position'], 'sentence_no': sentence_i, 'tag': 'error', 'error': errors[i], 'text': tags[j]['text'].substring(errors[i]['position'], errors[i]['position'] + errors[i]['length']) };
                var after = {  'offset': tags[j]['offset'] + errors[i]['position'] + errors[i]['length'], 'sentence_no': sentence_i, 'tag': 'text', 'text': tags[j]['text'].substring(errors[i]['position'] + errors[i]['length']) };
                tags.splice(Number(j), 1, before, now, after)
                break
              }
            }
          }
          this.contents.push(tags)
        }
        console.log(this.contents)
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
  interval = null;
  ngOnDestroy() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
  updated_time = null;
  ngOnInit(): void {
    this.Update();
    this.interval = setInterval(() => {
      this.api.getDocumentStatus(this.no).subscribe((responseBody) => {
        if (this.updated_time != responseBody['updated_time']) {
          this.updated_time = responseBody['updated_time'];
          this.Update();
        }
      });
    }, 1000);
    document.onmouseup = () => {
      var start = 0;
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
          console.log(range);
          var sentence_no = Number(select.focusNode.parentElement.id.replace("sentence_", ""));
          for (var i in this.contents[sentence_no]) {
            if (this.contents[sentence_no][i]['tag'] == 'text') {
              var find = this.contents[sentence_no][i]['text'].toLowerCase().indexOf(select.toString().toLowerCase());
              if (find != -1) {
                start = this.contents[sentence_no][i]['offset'] + find;
              }

            }
          }
          console.log(start)
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

        elementList[1].addEventListener('click', this.addError.bind(this, Number(select.focusNode.parentElement.id.replace("sentence_", "")), created.innerText, start));
        document.getSelection().empty();
      }
    }
  }
}
