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
        '{"token": "0123456789"}',
      );
    }, 2000);
  }],
});

const offlineServer = newServer({
  post: ['/request-upload', function (xhr) {
    xhr.respond(404);
  }],
});

export const basic = () => {
  offlineServer.install();

  return {
    components: { Uploader },
    template: '<Uploader base-url="/" name="media"/>',
    destroyed () {
      offlineServer.remove();
    },
    i18n,
  };
};

export const limited = () => {
  offlineServer.install();

  return {
    components: { Uploader },
    template: `
      <Uploader
          base-url="/"
          name="media"
          :max-size="100 * 1024"
          :mimetypes="['image/png','image/jpeg']"
          :limit="1"
      />
    `,
    destroyed () {
      offlineServer.remove();
    },
    i18n,
  };
};

export const manualTrigger = () => {
  offlineServer.install();

  return {
    components: { Uploader },
    template: `
      <Uploader
          base-url="/"
          name="media"
          :limit="3"
          :automatic-upload="false"
      />
    `,
    destroyed () {
      offlineServer.remove();
    },
    i18n,
  };
};

export const withExistingValue = () => {
  goodServer.install();
  const documentMetadata = {
    mimetype: 'application/vnd.oasis.opendocument.text',
    size: 82381,
    url: './placeholder.odt',
    name: 'test document',
  };
  fetchMock.restore()
    .get('/metadata/12e68184-5cba-4b27-9988-609a6cc3be63', documentMetadata)
    .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', 200);
  return {
    components: { Uploader },
    template: `
      <Uploader
          base-url="/"
          name="media"
          :limit="5"
          :values="['12e68184-5cba-4b27-9988-609a6cc3be63']"
      />
    `,
    destroyed () {
      goodServer.remove();
    },
    i18n,
  };
};

export default {
  title: 'Uploader',
};
