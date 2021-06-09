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

import Uploader from './Uploader';
import { newServer } from 'mock-xmlhttprequest';
import { i18n } from './i18n';
import fetchMock from 'fetch-mock';

// XMLHttpRequest mock
const goodServer = newServer({
  post: ['/request-upload', function (xhr) {
    xhr.uploadProgress(4096);
    setTimeout(() => {
      xhr.uploadProgress(4096 * 5);
    }, 1000);
    setTimeout(() => {
      xhr.respond(
        200,
        { 'Content-Type': 'application/json' },
        '{"token": "12e68184-5cba-4b27-9988-609a6cc3be63"}',
      );
    }, 2000);
  }],
});

const UploadingServerTemplate = (args, { argTypes }) => {
  goodServer.install();
  const documentMetadata = args.metadata || {
    mimetype: 'application/vnd.oasis.opendocument.text',
    size: 82381,
    url: './placeholder.odt',
    name: 'test document',
  };
  fetchMock.restore()
    .get('/metadata/12e68184-5cba-4b27-9988-609a6cc3be63', documentMetadata)
    .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', 200);
  if (process.env.NODE_ENV === 'test') {
    // Mock jQuery for snapshots tests
    window.jQuery = jest.fn(() => ({
      modal: () => {},
      on: () => {},
    }));
  }
  return ({
    components: { Uploader },
    props: Object.keys(argTypes),
    template: '<Uploader v-bind="$props" />',
    destroyed () {
      goodServer.remove();
      fetchMock.restore();
    },
    i18n,
  });
};

export const basic = UploadingServerTemplate.bind({});
basic.args = {
  baseUrl: '/',
  name: 'media',
};

export const limited = UploadingServerTemplate.bind({});
limited.args = {
  ...basic.args,
  maxSize: 100 * 1024,
  mimeTypes: ['image/png', 'image/jpeg'],
  limit: 1,
};

export const manualTrigger = UploadingServerTemplate.bind({});
manualTrigger.args = {
  ...basic.args,
  automaticUpload: false,
};

export const withExistingValue = UploadingServerTemplate.bind({});
withExistingValue.args = {
  ...basic.args,
  values: ['12e68184-5cba-4b27-9988-609a6cc3be63'],
  limit: 5,
};

export const editableImage = UploadingServerTemplate.bind({});
editableImage.args = {
  ...basic.args,
  values: ['12e68184-5cba-4b27-9988-609a6cc3be63'],
  metadata: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: './placeholder.jpeg',
    name: 'test image',
  },
};

export default {
  title: 'Uploader',
};
