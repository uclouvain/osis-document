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

import DocumentUploader from './DocumentUploader.vue';
import {newServer} from 'mock-xmlhttprequest';
import fetchMock from 'fetch-mock';
import type {MockResponse} from 'fetch-mock';
import type {Meta, StoryFn} from "@storybook/vue3";
import type {FileUpload} from "./interfaces";

// XMLHttpRequest mock
const mockXhrServer = newServer({
  post: ['/request-upload', function (xhr) {
    xhr.uploadProgress(4096);
    setTimeout(() => {
      xhr.uploadProgress(4096 * 5);
    }, 1000);
    setTimeout(() => {
      xhr.respond(
          200,
          {'Content-Type': 'application/json'},
          '{"token": "12e68184-5cba-4b27-9988-609a6cc3be63"}',
      );
    }, 2000);
  }],
});

const UploadingServerTemplate: StoryFn<typeof DocumentUploader & { metadata: FileUpload | MockResponse, changed: MockResponse }> = (
    {metadata, changed, ...args},
) => {
  mockXhrServer.install();
  const documentMetadata = metadata || {
    mimetype: 'application/vnd.oasis.opendocument.text',
    size: 82381,
    url: './placeholder.odt',
    name: 'test document.odt',
  };
  fetchMock
      .restore()
      .get('/metadata/12e68184-5cba-4b27-9988-609a6cc3be63', documentMetadata)
      .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', changed || 200);

  return ({
    components: {DocumentUploader},
    setup() {
      return {args};
    },
    template: '<DocumentUploader v-bind="args" base-url="/" name="media" />',
  });
};

export const Basic = UploadingServerTemplate.bind({});

export const Limited = UploadingServerTemplate.bind({});
Limited.args = {
  ...Basic.args,
  maxSize: 100 * 1024,
  mimetypes: ['image/png', 'image/jpeg'],
};

export const ManualTrigger = UploadingServerTemplate.bind({});
ManualTrigger.args = {
  ...Basic.args,
  automaticUpload: false,
};

export const WithExistingValue = UploadingServerTemplate.bind({});
WithExistingValue.args = {
  ...Basic.args,
  values: ['12e68184-5cba-4b27-9988-609a6cc3be63'],
};

export const EditableImage = UploadingServerTemplate.bind({});
EditableImage.args = {
  ...Basic.args,
  values: ['12e68184-5cba-4b27-9988-609a6cc3be63'],
  metadata: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: './placeholder.jpeg',
    name: 'test image.jpeg',
  },
};

export const EditableImageWithError = UploadingServerTemplate.bind({});
EditableImageWithError.args = {
  ...EditableImage.args,
  changed: 400,
};

export default {
  title: 'DocumentUploader',
  component: DocumentUploader,
} as Meta<typeof DocumentUploader>;
