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
import ViewEntry from './ViewEntry.vue';
import fetchMock from 'fetch-mock';
import Vue from 'vue';

jest.useFakeTimers();

afterEach(() => {
  fetchMock.restore();
});

it('should mount', () => {
  const wrapper = mount(ViewEntry, {
    propsData: {
      value: 'dummytoken',
      id: '2',
      baseUrl: '/',
    },
    mocks: {
      $t: k => k,
    },
  });
  expect(wrapper.text()).toContain('view_entry.loading');
});

describe('file is displayed', () => {
  async function setUp () {
    const documentMetadata = {
      mimetype: 'application/vnd.oasis.opendocument.text',
      size: 82381,
      url: './placeholder.odt',
      name: 'test document.odt',
    };

    fetchMock.get('/metadata/dummytoken', documentMetadata);

    const wrapper = mount(ViewEntry, {
      propsData: {
        value: 'dummytoken',
        id: '2',
        baseUrl: '/',
      },
      mocks: {
        $t: k => k,
      },
    });
    expect(wrapper.text()).toContain('view_entry.loading');
    await Vue.nextTick(); // wait for request
    await Vue.nextTick(); // wait for loading
    await Vue.nextTick(); // wait for re-rendering
    expect(wrapper.text()).toContain('application/vnd.oasis.opendocument.text');

    const input = wrapper.find('input[type=text]');
    expect(input.element.value).toBe('test document');
    expect(input.exists()).toBe(true);
    await input.setValue('new name');

    const displayedExtension = wrapper.find('.input-group-addon');
    expect(displayedExtension.exists()).toBe(true);
    expect(displayedExtension.element.textContent).toContain('.odt');

    return wrapper;
  }

  it('should update name without error', async () => {
    const wrapper = await setUp();
    fetchMock.post('/change-metadata/dummytoken', 200);
    await wrapper.find('.input-group-btn button').trigger('click');
    await Vue.nextTick(); // wait for request
    expect(wrapper.vm.file.name).toBe('new name.odt');
  });

  it('should show http error', async () => {
    const wrapper = await setUp();
    fetchMock.post('/change-metadata/dummytoken', 400);
    await wrapper.find('.input-group-btn button').trigger('click');
    await Vue.nextTick(); // wait for request
    expect(wrapper.vm.file.name).not.toBe('new name.odt');
    expect(wrapper.vm.error).toBeTruthy();
  });

  it('should show file infected error', async () => {
    const wrapper = mount(ViewEntry, {
      propsData: {
        value: 'FileInfectedException',
        id: '2',
        baseUrl: '/',
      },
      mocks: {
        $t: k => k,
      },
    });
    await Vue.nextTick(); // wait for request
    expect(wrapper.vm.error).toBeTruthy();
  });

  it('should show other errors', async () => {
    const wrapper = await setUp();
    fetchMock.post('/change-metadata/dummytoken', { throws: new Error('Network fail') });
    await wrapper.find('.input-group-btn button').trigger('click');
    await Vue.nextTick(); // wait for request
    expect(wrapper.vm.file.name).not.toBe('new name.odt');
    expect(wrapper.vm.error).toBeTruthy();
  });

  describe('should have a valid name and extension depending of the full filename', () => {
    test('if the fullname is empty', async () => {
      const wrapper = await setUp();
      wrapper.vm.fullName = '';
      await Vue.nextTick();
      expect(wrapper.vm.name).toBe('');
      expect(wrapper.vm.extension).toBe('');
    });

    test('if the fullname has no dot', async () => {
      const wrapper = await setUp();
      wrapper.vm.fullName = 'my_file';
      await Vue.nextTick();
      expect(wrapper.vm.name).toBe('my_file');
      expect(wrapper.vm.extension).toBe('');
    });

    test('if the fullname has no extension', async () => {
      const wrapper = await setUp();
      wrapper.vm.fullName = 'my_file.';
      await Vue.nextTick();
      expect(wrapper.vm.name).toBe('my_file.');
      expect(wrapper.vm.extension).toBe('');
    });

    test('if the fullname has a name and an extension, separated by a dot', async () => {
      const wrapper = await setUp();
      wrapper.vm.fullName = 'my_file.txt';
      await Vue.nextTick();
      expect(wrapper.vm.name).toBe('my_file');
      expect(wrapper.vm.extension).toBe('.txt');
    });

    test('if the fullname has a name (containing a dot) and an extension, separated by a dot', async () => {
      const wrapper = await setUp();
      wrapper.vm.fullName = 'my.file.txt';
      await Vue.nextTick();
      expect(wrapper.vm.name).toBe('my.file');
      expect(wrapper.vm.extension).toBe('.txt');
    });
  });
});
