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

import {flushPromises, mount} from '@vue/test-utils';
import UploadEntry from './UploadEntry.vue';
import {newServer} from 'mock-xmlhttprequest';
import {expect, it, vi} from "vitest";
import {nextTick} from "vue";

vi.useFakeTimers();
vi.mock('../utils.js');

const props = {
  file: new File([], 'foobar.png', {
    type: 'image/png',
  }),
  baseUrl: '/',
  automatic: false,
};


it('should mount', async () => {
  const createUrl = vi.fn(() => 'http://localhost/dummyurl');
  window.URL.createObjectURL = createUrl;
  const revokeUrl = vi.fn();
  window.URL.revokeObjectURL = revokeUrl;

  const wrapper = mount(UploadEntry, {props});
  await nextTick();
  expect(wrapper.text()).toContain('image/png');
  expect(wrapper.text()).toContain('foobar.png');
  expect(createUrl).toHaveBeenCalled();
  const image = wrapper.find('img');
  expect(image.element.src).toEqual('http://localhost/dummyurl');
  await image.trigger('load');
  expect(revokeUrl).toHaveBeenCalled();
});

it('should be deletable', async () => {
  window.URL.createObjectURL = vi.fn(() => 'http://localhost/dummyurl');

  const wrapper = mount(UploadEntry, {props});
  await wrapper.find('.btn-danger').trigger('click');
  expect(wrapper.emitted()).toHaveProperty('delete');
});

it('should display too large error', async () => {
  const wrapper = mount(UploadEntry, {
    props: {
      file: new File([new ArrayBuffer(1024)], 'foobar.png', {
        type: 'image/png',
      }),
      baseUrl: '/',
      maxSize: 150,
    },
  });
  await nextTick();
  expect(wrapper.text()).toContain('upload_entry.too_large');
  expect(wrapper.emitted()).toEqual({});
});

it('should display wrong type error', async () => {
  const wrapper = mount(UploadEntry, {
    props: {
      file: new File([], 'foobar.pdf', {
        type: 'application/pdf',
      }),
      baseUrl: '/',
      mimetypes: ['image/png', 'image/jpeg'],
    },
  });
  await nextTick();
  expect(wrapper.text()).toContain('upload_entry.wrong_type');
  expect(wrapper.emitted()).toEqual({});
});


it('should upload', async () => {
  vi.useFakeTimers();
  // Mocks
  const server = newServer({
    post: ['http://dummyhost/request-upload', function (xhr) {
      xhr.uploadProgress(512); // 50 % of 1024 bytes
      setTimeout(() => {
        xhr.uploadProgress(1024);// 100 % of 1024 bytes
        setTimeout(() => {
          xhr.respond(
              200,
              {'Content-Type': 'application/json'},
              '{"token": "0123456789"}',
          );
        });
      });
    }],
  }).install();

  const wrapper = mount(UploadEntry, {
    props: {
      file: new File([new ArrayBuffer(1024)], 'foobar.png', {
        type: 'image/png',
      }),
      baseUrl: 'http://dummyhost/',
    },
    unmounted() {
      server.remove();
    },
  });
  await flushPromises();

  expect(server.getRequestLog()).toHaveLength(1);
  expect(wrapper.find('.progress-bar-striped.active').exists()).toBe(true);
  vi.runAllTimers();
  expect(wrapper.emitted()).toHaveProperty('setToken.0', ['0123456789']);
});

it('should fail upload displaying message', async () => {
  // Mocks
  const server = newServer({
    post: ['http://dummyhost/request-upload', function (xhr) {
        xhr.respond(
            400,
            {'Content-Type': 'application/json'},
            '{"error": "NOPE", "detail": "Too many requests"}',
        );
    }],
  }).install();

  const wrapper = mount(UploadEntry, {
    props: {
      file: new File([new ArrayBuffer(1024)], 'foobar.png', {
        type: 'image/png',
      }),
      baseUrl: 'http://dummyhost/',
    },
    unmounted() {
      server.remove();
    },
  });
  await flushPromises();

  expect(server.getRequestLog()).toHaveLength(1);
  vi.runAllTimers();
  await flushPromises();
  expect(wrapper.emitted()).not.toHaveProperty('setToken');
  expect(wrapper.find('.btn-danger').exists()).toBe(true);
  expect(wrapper.find('.text-danger').text()).toBe("request_error");
});

it('should not upload with cropping enabled', async () => {
  vi.useFakeTimers();
  // Mocks
  const server = newServer({
    post: ['http://dummyhost/request-upload', function (xhr) {
      xhr.uploadProgress(512); // 50 % of 1024 bytes
      setTimeout(() => {
        xhr.uploadProgress(1024);// 100 % of 1024 bytes
        setTimeout(() => {
          xhr.respond(
              200,
              {'Content-Type': 'application/json'},
              '{"token": "0123456789"}',
          );
        });
      });
    }],
  }).install();

  const wrapper = mount(UploadEntry, {
    props: {
      file: new File([new ArrayBuffer(1024)], 'foobar.png', {
        type: 'image/png',
      }),
      baseUrl: 'http://dummyhost/',
      withCropping: true,
    },
    unmounted() {
      server.remove();
    },
  });
  await flushPromises();

  expect(server.getRequestLog()).toHaveLength(0);
});
