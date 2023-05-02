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

import DocumentEditor from './DocumentEditor.vue';
import fetchMock from 'fetch-mock';
import type {MockResponse} from 'fetch-mock';
import type {Meta, StoryFn} from "@storybook/vue3";
import type {FileUpload} from "./interfaces";

const UploadingServerTemplate: StoryFn<typeof DocumentEditor & {
  metadata: FileUpload | MockResponse,
  changed: MockResponse
}> = (
    {metadata, changed, ...args},
) => {
  const documentMetadata = metadata || {
    mimetype: 'application/pdf',
    size: 82381,
    url: './multiple-pages.pdf',
    name: 'test document.pdf',
  };
  fetchMock.config.fallbackToNetwork = true;  // to effectively download PDF
  fetchMock
      .restore()
      .get('/metadata/12e68184-5cba-4b27-9988-609a6cc3be63', documentMetadata)
      .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', changed || 200)
      .post('/save-editor/12e68184-5cba-4b27-9988-609a6cc3be63',
          {token: '12e68184-5cba-4b27-9988-609a6cc3be63'},
          {delay: 1000},
      );

  return ({
    components: {DocumentEditor},
    setup() {
      return {args};
    },
    template: '<DocumentEditor v-bind="args" base-url="/" value="12e68184-5cba-4b27-9988-609a6cc3be63" />',
  });
};

export const Basic = UploadingServerTemplate.bind({});

export default {
  title: 'DocumentEditor',
  component: DocumentEditor,
} as Meta<typeof DocumentEditor>;
