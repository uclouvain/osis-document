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

import {createLocalVue, mount, shallowMount} from '@vue/test-utils';
import { i18n } from './i18n';
import VueI18n from 'vue-i18n';
import Uploader from './Uploader.vue';
import UploadEntry from './components/UploadEntry';
import Vue from 'vue';
import EventBus from './event-bus.js';

jest.mock('./utils.js');
jest.mock('./event-bus.js');

it('should mount', () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      baseUrl: '/',
      maxSize: 1024,
    },
    mocks: {
      $t: (k) => k,
      $tc: (k) => k,
    },
  });
  expect(wrapper.text()).toContain('uploader.drag_n_drop_label');
  expect(wrapper.text()).toContain('uploader.add_file_label');
  expect(wrapper.text()).toContain('uploader.max_size_label');
});

it('should add upload entry', async () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      baseUrl: '/',
      automaticUpload: false,
    },
    mocks: {
      $t: (k) => k,
      $tc: (k) => k,
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

describe('file already uploaded', function () {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      baseUrl: '/',
      automaticUpload: false,
    },
    mocks: {
      $t: (k) => k,
      $tc: (k) => k,
    },
  });

  const file = new File([new ArrayBuffer(1)], 'file.jpg');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: jest.fn(() => [file]),
  });
  input.trigger('change');

  it('should add another file', async () => {
    input.trigger('change');
    await Vue.nextTick();
    expect(wrapper.findAllComponents(UploadEntry).length).toBe(2);
  });

  it('should delete token when file is deleted', async () => {
    expect(wrapper.findAllComponents(UploadEntry).length).toBe(2);
    expect(Object.values(wrapper.vm.tokens)).toHaveLength(2);

    wrapper.findAllComponents(UploadEntry).at(0).vm.$emit('delete');
    await Vue.nextTick();
    expect(wrapper.findAllComponents(UploadEntry)).toHaveLength(1);
    expect(Object.values(wrapper.vm.tokens)).toHaveLength(1);
  });
});

it('triggers upload when manual', async () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      baseUrl: '/',
      automaticUpload: false,
    },
    mocks: {
      $t: (k) => k,
      $tc: (k) => k,
    },
  });

  const file = new File([new ArrayBuffer(1)], 'file.jpg');
  const input = wrapper.find('input[type="file"]');
  Object.defineProperty(input.element, 'files', {
    get: jest.fn(() => [file]),
  });
  input.trigger('change');
  await Vue.nextTick();
  wrapper.find('button.pull-right').trigger('click');
  await Vue.nextTick();
  expect(EventBus.$on).toHaveBeenCalled();
});

it('should handle existing value', async () => {
  const wrapper = mount(Uploader, {
    propsData: {
      name: 'media',
      baseUrl: '/',
      values: ['0123456789'],
    },
    mocks: {
      $t: (k) => k,
      $tc: (k) => k,
    },
  });

  expect(wrapper.vm.tokens).toEqual({ 1: '0123456789' });
});

describe('must return the right drag-and-drop label', () => {
  let wrapper;

  beforeAll(() => {
    // Create a local vue to test the translations
    const localVue = createLocalVue();
    localVue.use(VueI18n);
    // Create wrapper
    wrapper = shallowMount(Uploader, {
      propsData: {
        name: 'media',
        baseUrl: '/',
        values: ['0123456789'],
      },
      i18n,
      localVue,
    });
  });

  it('with an undefined maximum limit and undefined minimum limit', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: undefined,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Drag and drop file(s) here');
  });

  it('with an undefined maximum limit and defined but not reached minimum limit (1 missing)', async () => {
    await wrapper.setProps({
      minFiles: 2,
      maxFiles: undefined,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Please drag and drop here at least one additional file');
  });

  it('with an undefined maximum limit and defined but not reached minimum limit (more than 1 missing)', async () => {
    await wrapper.setProps({
      minFiles: 3,
      maxFiles: undefined,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Please drag and drop here at least 2 additional files');
  });

  it('with an undefined maximum limit and defined and reached minimum limit', async () => {
    await wrapper.setProps({
      minFiles: 1,
      maxFiles: undefined,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Drag and drop file(s) here');
  });

  it('with an undefined minimum limit and defined but not reached maximum limit (1 missing)', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: 2,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Drag and drop file(s) here (up to one)');
  });

  it('with an undefined minimum limit and defined but not reached maximum limit (more than 1 missing)', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: 3,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Drag and drop file(s) here (up to 2)');
  });

  it('with an undefined minimum limit and defined and reached maximum limit', async () => {
    await wrapper.setProps({
      minFiles: undefined,
      maxFiles: 1,
    });
    expect(wrapper.find('.dropzone').exists()).toBe(false);
  });

  it('with defined and reached minimum and maximum limits', async () => {
    await wrapper.setProps({
      minFiles: 1,
      maxFiles: 1,
    });
    expect(wrapper.find('.dropzone').exists()).toBe(false);
  });

  it('with defined minimum (reached) and maximum (not reached) limits', async () => {
    await wrapper.setProps({
      minFiles: 1,
      maxFiles: 3,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Drag and drop file(s) here (up to 2)');
  });

  it('with defined minimum (not reached) and maximum (not reached) limits', async () => {
    await wrapper.setProps({
      minFiles: 2,
      maxFiles: 3,
    });
    const dropZoneText = wrapper.find('.dropzone').text();
    expect(dropZoneText).toContain('Please drag and drop here at least one additional file (up to 2)');
  });
});
