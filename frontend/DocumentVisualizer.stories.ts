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

import DocumentVisualizer from './DocumentVisualizer.vue';
import type {MockResponse} from 'fetch-mock';
import fetchMock from 'fetch-mock';
import type {Meta, StoryFn} from "@storybook/vue3";

const VisualizerTemplate: StoryFn<typeof DocumentVisualizer & { response: MockResponse }> = ({response, ...args}) => {
  fetchMock.restore();
  if (response) {
    fetchMock.get('*', response);
  }
  return {
    components: {DocumentVisualizer},
    setup() {
      return {args};
    },
    template: '<DocumentVisualizer base-url="/" :values="[]" v-bind="args" />',
  };
};

export const Empty = VisualizerTemplate.bind({});

export const Basic = VisualizerTemplate.bind({});
Basic.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'application/vnd.oasis.opendocument.text',
    size: 82381,
    url: './placeholder.odt',
    name: 'test document',
  },
};

export const PDF = VisualizerTemplate.bind({});
PDF.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'application/pdf',
    size: 82381,
    url: './placeholder.pdf',
    name: 'test document',
  },
};

export const Image = VisualizerTemplate.bind({});
Image.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'image/jpeg',
    size: 38329,
    url: './placeholder.jpeg',
    name: 'test image',
  },
};

export const Loading = VisualizerTemplate.bind({});
Loading.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: new Promise(res => setTimeout(() => res(200), 2000000)),
};

export const NotFound = VisualizerTemplate.bind({});
NotFound.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: 404,
};


export default {
  title: 'DocumentVisualizer',
  component: DocumentVisualizer,
} as Meta<typeof DocumentVisualizer>;
