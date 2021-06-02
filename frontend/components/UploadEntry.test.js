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

import Vue from 'vue';
import { mount } from '@vue/test-utils';
import UploadEntry from './UploadEntry.vue';
import { newServer } from 'mock-xmlhttprequest';

jest.mock('../utils.js');

it('should mount', () => {
  window.URL.createObjectURL = jest.fn();
  const wrapper = mount(UploadEntry, {
    propsData: {
      file: new File([], 'foobar.png', {
        type: 'image/png',
      }),
      uploadUrl: '',
    },
    mocks: {
      $t: k => k,
    },
  });
  expect(wrapper.text()).toContain('image/png');
  expect(wrapper.text()).toContain('foobar.png');
});

it('should display error', async () => {
  const wrapper = mount(UploadEntry, {
    propsData: {
      file: new File(Array(1024).fill('foobar'), 'foobar.png', {
        type: 'image/png',
      }),
      uploadUrl: '',
      maxSize: 150,
    },
    mocks: {
      $t: k => k,
    },
  });
  await Vue.nextTick();
  expect(wrapper.text()).toContain('upload_entry.too_large');
});

it('should display error', async () => {
  const wrapper = mount(UploadEntry, {
    propsData: {
      file: new File([], 'foobar.pdf', {
        type: 'application/pdf',
      }),
      uploadUrl: '',
      mimetypes: ['image/png', 'image/jpeg'],
    },
    mocks: {
      $t: k => k,
    },
  });
  await Vue.nextTick();
  expect(wrapper.text()).toContain('upload_entry.wrong_type');
});

jest.useFakeTimers();

it('should upload', async () => {
  // Mocks
  const server = newServer({
    post: ['http://dummyhost/upload', function (xhr) {
      xhr.uploadProgress(4096);
      xhr.respond(
        200,
        { 'Content-Type': 'application/json' },
        '{"token": "0123456789"}',
      );
    }],
  }).install();
  window.URL.createObjectURL = jest.fn(() => 'http://localhost/dummyurl');
  window.URL.revokeObjectURL = jest.fn();

  const wrapper = mount(UploadEntry, {
    propsData: {
      file: new File([new ArrayBuffer(1)], 'foobar.png', {
        type: 'image/png',
      }),
      uploadUrl: 'http://dummyhost/upload',
    },
    mocks: {
      $t: k => k,
    },
    destroyed () {
      server.remove();
    },
  });
  await Vue.nextTick();
  jest.runAllTimers();
  expect(wrapper.emitted()['set-token'][0]).toEqual(['0123456789']);
  expect(window.URL.createObjectURL).toHaveBeenCalled();

  const image = wrapper.find('img');
  expect(image.element.src).toEqual('http://localhost/dummyurl');
  image.trigger('load');
  expect(window.URL.revokeObjectURL).toHaveBeenCalled();
});
