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

import { mount } from '@vue/test-utils';
import Uploader from './Uploader.vue';
import UploadEntry from './components/UploadEntry';
import Vue from 'vue';

it('should mount', () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      uploadUrl: '/upload',
    },
  });
  expect(wrapper.text()).toContain('Glisser-déposer un ou plusieurs fichiers ici');
});

it('should add upload entry', async () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      uploadUrl: '/upload',
    },
  });
  expect(wrapper.findComponent(UploadEntry).exists()).toBe(false);

  const file = new File([new ArrayBuffer(1)], 'file.jpg');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: jest.fn(() => [file]),
  });
  input.trigger('change');
  await Vue.nextTick();
  expect(wrapper.findComponent(UploadEntry).exists()).toBe(true);
});
