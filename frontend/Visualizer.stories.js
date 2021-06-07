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

import Visualizer from './Visualizer';
import fetchMock from 'fetch-mock';
import { i18n } from './i18n';

const documentMetadata = {
  mimetype: 'application/vnd.oasis.opendocument.text',
  size: 82381,
  url: './placeholder.odt',
  name: 'test document',
};
const pdfMetadata = {
  mimetype: 'application/pdf',
  size: 82381,
  url: './placeholder.pdf',
  name: 'test document',
};
const imageMetadata = {
  mimetype: 'image/jpeg',
  size: 38329,
  url: './placeholder.jpeg',
  name: 'test image',
};

export const empty = () => {
  return {
    components: { Visualizer },
    template: `
      <Visualizer base-url="/"/>`,
  };
};

export const basic = () => {
  fetchMock.restore()
    .get('/metadata/77d4b8f6-ee55-4c40-b118-e9fffd796198', documentMetadata);

  return {
    components: { Visualizer },
    template: `
      <Visualizer :values="['77d4b8f6-ee55-4c40-b118-e9fffd796198']" base-url="/" />`,
    i18n,
  };
};

export const pdf = () => {
  fetchMock.restore()
    .get('/metadata/77d4b8f6-ee55-4c40-b118-e9fffd796198', pdfMetadata);

  return {
    components: { Visualizer },
    template: `
      <Visualizer :values="['77d4b8f6-ee55-4c40-b118-e9fffd796198']" base-url="/"/>`,
    i18n,
  };
};
export const image = () => {
  fetchMock.restore()
    .get('/metadata/77d4b8f6-ee55-4c40-b118-e9fffd796198', imageMetadata);

  return {
    components: { Visualizer },
    template: `
      <Visualizer :values="['77d4b8f6-ee55-4c40-b118-e9fffd796198']" base-url="/"/>`,
    i18n,
  };
};

export const loading = () => {
  fetchMock.restore()
    .get('/metadata/77d4b8f6-ee55-4c40-b118-e9fffd796198',
      new Promise(res => setTimeout(() => res(200), 2000000)),
    );

  return {
    components: { Visualizer },
    template: `
      <Visualizer :values="['77d4b8f6-ee55-4c40-b118-e9fffd796198']" base-url="/"/>`,
    i18n,
  };
};

export const notFound = () => {
  fetchMock.restore()
    .get('/metadata/77d4b8f6-ee55-4c40-b118-e9fffd796198', 404);

  return {
    components: { Visualizer },
    template: `
      <Visualizer :values="['77d4b8f6-ee55-4c40-b118-e9fffd796198']" base-url="/"/>`,
    i18n,
  };
};

export default {
  title: 'Visualizer',
};
