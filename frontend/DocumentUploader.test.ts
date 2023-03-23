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

import {mount, shallowMount} from '@vue/test-utils';
import {i18n} from './i18n';
import DocumentUploader from './DocumentUploader.vue';
import EventBus from './event-bus';
import {describe, expect, it, test, vi} from "vitest";
import {nextTick} from "vue";
import UploadEntry from "./components/UploadEntry.vue";
import ViewEntry from "./components/ViewEntry.vue";

vi.mock('./utils.js');
vi.mock('./event-bus.js');


let changeHandler: unknown;
const on = vi.fn((eventName, handler: CallableFunction) => {
  changeHandler = handler;
});
const val = vi.fn();
const jQueryMock = vi.fn(() => ({
  val: val,
  on: on,
}));

vi.stubGlobal('jQuery', jQueryMock);

const props = {
  name: 'media',
  baseUrl: '/',
  automaticUpload: false,
};


it('should mount', () => {
  const wrapper = mount(DocumentUploader, {
    props: {
      ...props,
      maxSize: 1024,
      mimetypes: ['image/png'],
    },
  });
  expect(wrapper.text()).toContain('uploader.drag_n_drop_label');
  expect(wrapper.text()).toContain('uploader.add_file_label');
  expect(wrapper.text()).toContain('uploader.max_size_label');
});

it('should add upload entry', async () => {
  const wrapper = mount(DocumentUploader, {props});
  expect(wrapper.findComponent({name: 'UploadEntry'}).exists()).toBe(false);

  const file = new File([new ArrayBuffer(1)], 'file.jpg');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: vi.fn(() => [file]),
  });
  await input.trigger('change');
  expect(wrapper.findComponent({name: 'UploadEntry'}).exists()).toBe(true);

  // When token is known, should be transformed into view entry
  wrapper.getComponent(UploadEntry).vm.$emit('setToken', 'sometoken');
  await nextTick();
  expect(wrapper.findComponent({name: 'UploadEntry'}).exists()).toBe(false);
  expect(wrapper.findComponent({name: 'ViewEntry'}).exists()).toBe(true);
});

describe('file already uploaded', async () => {
  const wrapper = mount(DocumentUploader, {props});

  const file = new File([new ArrayBuffer(1)], 'file.jpg');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: vi.fn(() => [file]),
  });
  await input.trigger('change');

  it('should add another file', async () => {
    await input.trigger('change');
    expect(wrapper.findAllComponents({name: 'UploadEntry'}).length).toBe(2);
  });

  it('should delete token when file is deleted', async () => {
    expect(wrapper.findAllComponents({name: 'UploadEntry'}).length).toBe(2);

    await wrapper.findAllComponents({name: 'UploadEntry'})[0].find('.btn-danger').trigger('click');
    expect(wrapper.findAllComponents({name: 'UploadEntry'})).toHaveLength(1);
  });
});

it('should trigger upload when manual', async () => {
  const wrapper = mount(DocumentUploader, {props});

  const eventBusOn = vi.spyOn(EventBus, 'on');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: vi.fn(() => [new File([new ArrayBuffer(1)], 'file.jpg')]),
  });
  await input.trigger('change');
  await wrapper.find('.text-right button').trigger('click');
  expect(eventBusOn).toHaveBeenCalled();
});

it('should handle existing value', async () => {
  const wrapper = mount(DocumentUploader, {
    props: {
      ...props,
      values: ['0123456789'],
    },
  });

  expect(wrapper.findAllComponents({name: 'ViewEntry'}).length).toBe(1);
  const entry = wrapper.getComponent(ViewEntry);
  expect(entry.props('value')).toBe('0123456789');
  expect(entry.props('id')).toBe("media-1");

  // When entry is updated, so is the tokens list
  entry.vm.$emit('updateToken', 'newtoken');
  await nextTick();
  expect(entry.props('value')).toBe('newtoken');

  // When entry is deleted, the tokens list is refreshed
  entry.vm.$emit('delete');
  await nextTick();
  expect(wrapper.findAllComponents({name: 'ViewEntry'}).length).toBe(0);
});

describe('must return the right drag-and-drop label', () => {
  // Create wrapper
  const wrapper = shallowMount(DocumentUploader, {
    props: {
      ...props,
      values: ['0123456789'],
    },
    global: {
      mocks: {
        // use real i18n
        $t: i18n.global.t,
        $tc: i18n.global.tc,
      },
    },
  });

  test('with an undefined maximum limit and undefined minimum limit', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: undefined,
    });
    expect(wrapper.get('.dropzone').text()).toContain('Drag and drop your files here');
  });

  test('with an undefined maximum limit and defined minimum limit', async () => {
    await wrapper.setProps({
      minFiles: 2,
      maxFiles: undefined,
    });
    expect(wrapper.get('.dropzone').text()).toContain('Drag and drop at least 2 files here');
  });

  test('with an undefined minimum limit and defined maximum limit', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: 2,
    });
    expect(wrapper.get('.dropzone').text()).toContain('Drag and drop your files here (maximum 2)');
  });

  test('with defined and reached minimum and maximum limits', async () => {
    await wrapper.setProps({
      minFiles: 1,
      maxFiles: 1,
    });
    expect(wrapper.find('.dropzone').exists()).toBe(false);
  });

  test('with specific minimum and maximum limits', async () => {
    await wrapper.setProps({
      minFiles: 2,
      maxFiles: 2,
    });
    expect(wrapper.get('.dropzone').text()).toContain("Drag and drop 2 files here");
  });

  test('with defined minimum limit and greater maximum limit', async () => {
    await wrapper.setProps({
      minFiles: 2,
      maxFiles: 3,
    });
    expect(wrapper.get('.dropzone').text()).toContain("Drag and drop between 2 and 3 files here");
  });
});

it('should trigger events', async () => {
  const wrapper = mount(DocumentUploader, {
    props: {
      ...props,
      values: ['0123456789'],
    },
  });
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  const spy = vi.spyOn(wrapper.vm.$el, 'dispatchEvent');

  // setData does a deep merge, so we can't use it
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  wrapper.vm.$data.tokens = {};
  await nextTick(); // wait for refresh
  expect(spy).toHaveBeenCalled();
  expect(spy.mock.calls).toHaveProperty('0.0.type', 'osisdocument:delete');
  expect(spy.mock.calls).toHaveProperty('0.0.detail', {
    newTokens: {},
    oldTokens: {
      '1': '0123456789',
    },
  });

  spy.mockClear();
  await wrapper.setData({
    tokens: ['foo'],
  });
  expect(spy).toHaveBeenCalled();
  expect(spy.mock.calls).toHaveProperty('0.0.type', 'osisdocument:add');
  expect(spy.mock.calls).toHaveProperty('0.0.detail', {
    newTokens: {
      '0': 'foo',
    },
    oldTokens: {},
  });
});

it('should clear all tokens when an input is emptied', async () => {
  changeHandler = undefined;
  on.mockClear();
  const wrapper = mount(DocumentUploader, {
    props: {
      ...props,
      values: ['0123456789'],
    },
  });
  expect(changeHandler).toBeTruthy();
  expect(on.mock.calls).toHaveProperty('0.0', 'change');

  // If input is not empty, no changes
  val.mockReturnValue('not empty');
  (changeHandler as CallableFunction)({target: '<input type="file" name="foo">'});
  await nextTick();
  expect(wrapper.findAllComponents({name: 'ViewEntry'}).length).toBe(1);

  // If input is empty, delete all entries
  val.mockClear().mockReturnValue('');
  (changeHandler as CallableFunction)({target: '<input type="file" name="bar">'});
  await nextTick();
  expect(wrapper.findAllComponents({name: 'ViewEntry'}).length).toBe(0);
});

it('should handle dragging', async () => {
  const wrapper = mount(DocumentUploader, {props});
  await wrapper.find('input[type=file]').trigger('dragenter');
  expect(wrapper.find('.dropzone').classes()).toContain('hovering');
  await wrapper.find('input[type=file]').trigger('dragleave');
  expect(wrapper.find('.dropzone').classes()).not.toContain('hovering');
});

it('should react on add file button', async () => {
  const wrapper = mount(DocumentUploader, {props});
  const spy = vi.spyOn((wrapper.get('input[type=file]').element as HTMLInputElement), 'click');
  await wrapper.find('.dropzone .btn').trigger('click');
  expect(spy).toHaveBeenCalled();
});
