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

import { i18n } from '../i18n';
import fetchMock from 'fetch-mock';
import ViewingModal from './ViewingModal';

const ModalImageTemplate = (args, { argTypes }) => {
  fetchMock.restore()
    .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', 200)
    .post('/rotate-image/12e68184-5cba-4b27-9988-609a6cc3be63', 200);
  if (process.env.NODE_ENV === 'test') {
    // Mock jQuery for snapshots tests
    window.jQuery = jest.fn(() => ({
      modal: () => {},
      on: () => {},
    }));
  }
  return ({
    components: { ViewingModal },
    props: Object.keys(argTypes),
    template: '<ViewingModal v-bind="$props" />',
    destroyed () {
      fetchMock.restore();
    },
    i18n,
  });
};

export const landscape = ModalImageTemplate.bind({});
landscape.args = {
  baseUrl: '/',
  name: 'media',
  id: '1',
  file: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: './placeholder.jpeg',
    name: 'test image',
  },
  value: '12e68184-5cba-4b27-9988-609a6cc3be63',
  openOnMount: true,
};

export const portrait = ModalImageTemplate.bind({});
portrait.args = {
  ...landscape.args,
  file: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: './portrait.jpeg',
    name: 'test image',
  },
};

export default {
  title: 'ViewingModal',
};
