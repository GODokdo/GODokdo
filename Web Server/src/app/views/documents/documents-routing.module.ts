import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { DocumentPostComponent } from './document-post.component';
import { DocumentViewComponent } from './document-view.component';
import { DocumentsComponent } from './documents.component';


const routes: Routes = [
  {
    path: '',
    data: {
      title: 'Documents'
    },
    children: [
      {
        path: '',
        redirectTo: 'list'
      },
      {
        path: 'post',
        component: DocumentPostComponent,
        data: {
          title: '분석 작업 요청'
        }
      },
      {
        path: 'list',
        component: DocumentsComponent,
        data: {
          title: '모든 문서'
        }
      },
      {
        path: 'auto-labeling-list',
        component: DocumentsComponent,
        data: {
          title: '자동 분류된 문서'
        }
      },
      {
        path: 'view/:no',
        component: DocumentViewComponent,
        data: {
          title: '문서 열람'
        }
      }
    ]
  }
];


@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DocumentsRoutingModule { }
