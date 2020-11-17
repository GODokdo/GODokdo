import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DocumentsRoutingModule } from './documents-routing.module';
import { DocumentsComponent } from './documents.component';
import { DocumentViewComponent } from './document-view.component';
import { PopoverModule } from 'ngx-bootstrap/popover';
import { CollapseModule } from 'ngx-bootstrap/collapse';
import { TabsModule } from 'ngx-bootstrap/tabs';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { AlertModule } from 'ngx-bootstrap/alert';
import { ModalModule } from 'ngx-bootstrap/modal';
import { ReactiveFormsModule } from '@angular/forms';
import { DocumentPostComponent } from './document-post.component';


@NgModule({
  declarations: [DocumentsComponent, DocumentViewComponent, DocumentPostComponent],
  imports: [
    CommonModule,
    DocumentsRoutingModule,
    PopoverModule.forRoot(),
    CollapseModule.forRoot(),
    TabsModule,
    TooltipModule.forRoot(),
    AlertModule.forRoot(),
    ModalModule.forRoot(),
    ReactiveFormsModule
  ]
})
export class DocumentsModule { }
