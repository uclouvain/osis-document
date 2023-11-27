/*
 *
 *   OSIS stands for Open Student Information System. It's an application
 *   designed to manage the core business of higher education institutions,
 *   such as universities, faculties, institutes and professional schools.
 *   The core business involves the administration of students, teachers,
 *   courses, programs and so on.
 *
 *   Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   A copy of this license - GNU General Public License - is available
 *   at the root of the source code of this program.  If not,
 *   see http://www.gnu.org/licenses/.
 *
 */
// eslint-disable-next-line vue/prefer-import-from-vue
import {createApp} from '@vue/runtime-dom'; // So it can be spied on in tests
import {i18n} from './i18n';
import Uploader from './DocumentUploader.vue';
import Visualizer from './DocumentVisualizer.vue';


interface UploaderProps extends Record<string, unknown> {
  baseUrl: string,
  maxSize?: number,
  minFiles?: number,
  maxFiles?: number,
  mimetypes?: string[],
  values?: string[],
  automaticUpload?: boolean,
  editableFilename?: boolean,
  withCropping?: boolean,
}

interface VisualizerProps extends Record<string, unknown> {
  baseUrl: string,
  values: string[],
  postProcessStatus: string,
  getProgressUrl: string,
  baseUuid: string,
  wantedPostProcess: string,
}

function initDocumentComponents() {
  document.querySelectorAll<HTMLElement>('.osis-document-uploader:not([data-v-app])').forEach((elem) => {
    const props: UploaderProps = {baseUrl: "", ...elem.dataset};
    if (typeof elem.dataset.maxSize !== 'undefined') {
      props.maxSize = Number.parseInt(elem.dataset.maxSize);
    }
    if (typeof elem.dataset.minFiles !== 'undefined') {
      props.minFiles = Number.parseInt(elem.dataset.minFiles);
    }
    if (typeof elem.dataset.maxFiles !== 'undefined') {
      props.maxFiles = Number.parseInt(elem.dataset.maxFiles);
    }
    if (typeof elem.dataset.mimetypes !== 'undefined') {
      props.mimetypes = elem.dataset.mimetypes.split(',');
    }
    if (typeof elem.dataset.values !== 'undefined') {
      props.values = elem.dataset.values.split(',');
    }
    if (typeof elem.dataset.automaticUpload !== 'undefined') {
      props.automaticUpload = elem.dataset.automaticUpload === 'true';
    }
    if (typeof elem.dataset.editableFilename !== 'undefined') {
      props.editableFilename = elem.dataset.editableFilename === 'true';
    }
    if (typeof elem.dataset.withCropping !== 'undefined') {
      props.withCropping = elem.dataset.withCropping === 'true';
    }
    if (typeof elem.dataset.croppingOptions !== 'undefined') {
      props.croppingOptions = JSON.parse(elem.dataset.croppingOptions);
    }
    createApp(Uploader, props).use(i18n).mount(elem);
  });

  document.querySelectorAll<HTMLElement>('.osis-document-visualizer:not([data-v-app])').forEach((elem) => {
    const props: VisualizerProps = {baseUrl: "", values: [],postProcessStatus: "", getProgressUrl: "", baseUuid:"", wantedPostProcess:"",  ...elem.dataset};
    if (typeof elem.dataset.values !== 'undefined') {
      props.values = elem.dataset.values.split(',');
    }
    if (typeof elem.dataset.postProcessStatus !== 'undefined') {
      props.postProcessStatus = elem.dataset.postProcessStatus;
    }
    if (typeof elem.dataset.getProgressUrl !== 'undefined') {
      props.getProgressUrl = elem.dataset.getProgressUrl;
    }
    if (typeof elem.dataset.baseUuid !== 'undefined') {
      props.baseUuid = elem.dataset.baseUuid;
    }
    if (typeof elem.dataset.wantedPostProcess !== 'undefined') {
      props.wantedPostProcess = elem.dataset.wantedPostProcess;
    }
    createApp(Visualizer, props).use(i18n).mount(elem);
  });
}

// Initialize at first load
initDocumentComponents();

// Initialize later if nodes are added dynamically
const observer = new MutationObserver(initDocumentComponents);
observer.observe(document, {childList: true, subtree: true});
