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

import {flushPromises, mount, shallowMount} from '@vue/test-utils';
import ViewEntry from './ViewEntry.vue';
import fetchMock from 'fetch-mock';
import {afterEach, describe, expect, it, test} from "vitest";
import ViewingModal from "./ViewingModal.vue";
import {nextTick} from "vue";
import {uuid} from 'vue-uuid';

const props = {
  value: 'dummytoken',
  id: '2',
  baseUrl: '/',
  postProcessStatus: 'DONE',
  getProgressUrl: 'http://localhost:8000/api/osis-document/get-progress-async-post-processing/UUID',
  baseUuid: uuid.v4(),
  wantedPostProcess: '',
};

const documentMetadata = {
  mimetype: 'application/vnd.oasis.opendocument.text',
  size: 82381,
  url: './placeholder.odt',
  name: 'test document.odt',
};

const getRemoteTokenResponse = {
  access: 'READ',
  expires_at: '2023-07-24T14:46:07.839585',
  token: 'ImU3NTFjYTFlLTJhOWYtNDA2Yi1hNDIwLTlmY2FlYTJkNTlmOCI:1qNuiR:6EpSvOF0hfZTSx1WewDsM3WlT5F-tyola0H-qijV3ZE',
  upload_id: 'e751ca1e-2a9f-406b-a420-9fcaea2d59f8',
};

const getProgressResponse= {
  'progress': 100,
  'wanted_post_process': 'DONE',
};

afterEach(() => {
  fetchMock.restore();
});

it('should mount', () => {
  fetchMock.get('/metadata/dummytoken', documentMetadata);
  const wrapper = mount(ViewEntry, {props});
  expect(wrapper.text()).toContain('view_entry.loading');
});

describe('progress of post-processing is correctly displayed', () => {
  it('should show progress_bar of post-processing progress', async () => {
    fetchMock.get('http://localhost:8000/api/osis-document/get-progress-async-post-processing/UUID?wanted_post_process=MERGE', {
      'progress': 50,
      'wanted_post_process': 'DONE',
    });
    fetchMock.post('/read-token/'+props.baseUuid.toString(), getRemoteTokenResponse);
    fetchMock.get('/metadata/ImU3NTFjYTFlLTJhOWYtNDA2Yi1hNDIwLTlmY2FlYTJkNTlmOCI:1qNuiR:6EpSvOF0hfZTSx1WewDsM3WlT5F-tyola0H-qijV3ZE', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: '',
        isEditable: false,
        wantedPostProcess: 'MERGE',
        baseUrl: '/',
      },
      data() {
        return {
          loading: true,
          inPostProcessing: false,
          postProcessingProgress: 0,
          error: '',
          name: '',
          extension: '',
        };
      },
    });
    await flushPromises();
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.text()).toContain('Avancement du post processing : 50 %');
    expect(wrapper.vm.inPostProcessing).toBe(true);
  });

  it('should make get_progress request without wanted_post_process', async () => {
    fetchMock.get('http://localhost:8000/api/osis-document/get-progress-async-post-processing/UUID', getProgressResponse);
    fetchMock.post('/read-token/'+props.baseUuid.toString(), getRemoteTokenResponse);
    fetchMock.get('/metadata/ImU3NTFjYTFlLTJhOWYtNDA2Yi1hNDIwLTlmY2FlYTJkNTlmOCI:1qNuiR:6EpSvOF0hfZTSx1WewDsM3WlT5F-tyola0H-qijV3ZE', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: '',
        isEditable: false,
        baseUrl: '/',
      },
      data() {
        return {
          loading: true,
          inPostProcessing: false,
          postProcessingProgress: 50,
          error: '',
          name: '',
          extension: '',
        };
      },
    });
    await flushPromises();
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.vm.inPostProcessing).toBe(false);
    expect(wrapper.vm.postProcessingProgress).toBe(100);
  });

  it('should make get_progress request with wanted_post_process for DONE post_process', async () => {
    fetchMock.get('http://localhost:8000/api/osis-document/get-progress-async-post-processing/UUID?wanted_post_process=MERGE', {
      'progress': 100,
      'wanted_post_process': 'DONE',
    });
    fetchMock.post('/read-token/'+props.baseUuid.toString(), getRemoteTokenResponse);
    fetchMock.get('/metadata/ImU3NTFjYTFlLTJhOWYtNDA2Yi1hNDIwLTlmY2FlYTJkNTlmOCI:1qNuiR:6EpSvOF0hfZTSx1WewDsM3WlT5F-tyola0H-qijV3ZE', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: '',
        isEditable: false,
        baseUrl: '/',
        wantedPostProcess: 'MERGE',
      },
      data() {
        return {
          loading: true,
          inPostProcessing: false,
          postProcessingProgress: 50,
          error: '',
          name: '',
          extension: '',
        };
      },
    });
    await flushPromises();
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.vm.inPostProcessing).toBe(false);
  });

  it('should make get_progress request with wanted_post_process for PENDING post_process', async () => {
    fetchMock.get('/api/osis-document/get-progress-async-post-processing/UUID?pk=UUID', {
      'progress': 50,
      'wanted_post_process': 'PENDING',
    });
   const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: '',
        isEditable: false,
        baseUrl: '/',
        wantedPostProcess: 'MERGE',
      },
      data() {
        return {
          loading: true,
          inPostProcessing: false,
          postProcessingProgress: 0,
          error: '',
          name: '',
          extension: '',
        };
      },
    });
    await flushPromises();
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.vm.inPostProcessing).toBe(true);
  });
  it('should have hidde progress_bar of post-processing progress', async () => {
    fetchMock.get('/get-progress-async-post-processing/UUID', getProgressResponse);
    fetchMock.post('/read-token/'+props.baseUuid.toString(), getRemoteTokenResponse);
    fetchMock.get('/metadata/ImU3NTFjYTFlLTJhOWYtNDA2Yi1hNDIwLTlmY2FlYTJkNTlmOCI:1qNuiR:6EpSvOF0hfZTSx1WewDsM3WlT5F-tyola0H-qijV3ZE', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: '',
        isEditable: false,
      },
      data() {
        return {
          postProcessingProgress: 100,
        };
      },
    });
    await flushPromises();
    expect(wrapper.html()).not.contain('<div class="progress" style="text-align: center">');
    expect(wrapper.html()).contain('<div>test document.odt</div><small><span class="text-nowrap">80.45 KB</span> (application/vnd.oasis.opendocument.text)</small>');
    expect(wrapper.vm.error).toBe('');
    expect(wrapper.vm.inPostProcessing).toBe(false);
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.vm.file).not.toBe(null);
  });
  it('should have hidde component', async () => {
    fetchMock.get('/metadata/dummytoken', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        isEditable: false,
      },
    });
    await flushPromises();
    wrapper.unmount();
    expect(wrapper.html()).not.contain('<div class="progress" style="text-align: center">');
    expect(wrapper.text()).not.toContain('Avancement du post processing : 50 %');
  });
});

describe('file is correctly displayed', () => {
  it('should show basic file', async () => {
    fetchMock.get('/metadata/dummytoken', documentMetadata);
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        isEditable: false,
      },
    });
    await flushPromises();
    expect(wrapper.text()).toContain('application/vnd.oasis.opendocument.text');
    expect(wrapper.find('.btn-danger').exists()).toBe(false);
  });

  it('should show file infected error', async () => {
    const wrapper = mount(ViewEntry, {
      props: {
        ...props,
        value: 'FileInfectedException',
      },
    });
    await flushPromises();
    expect(wrapper.find('.text-danger').exists()).toBe(true);
    expect(wrapper.find('.btn-danger').exists()).toBe(true);
    await wrapper.get('button.btn-danger').trigger('click');
    expect(wrapper.emitted()).toHaveProperty('delete');
  });

  it('should show error', async () => {
    fetchMock.get('/metadata/dummytoken', 404);
    const wrapper = mount(ViewEntry, {props});
    await flushPromises();
    expect(wrapper.find('.text-danger').exists()).toBe(true);
    expect(wrapper.find('.btn-danger').exists()).toBe(true);
  });

  it('should show error but not deletable', async () => {
    fetchMock.get('/metadata/dummytoken', 404);
    const wrapper = mount(ViewEntry, {props: {...props, isEditable: false}});
    await flushPromises();
    expect(wrapper.find('.btn-danger').exists()).toBe(false);
  });
});

describe('file can be renamed', () => {
  async function setUp(override?: object) {
    fetchMock.restore().get('/metadata/dummytoken', {...documentMetadata, ...override});
    const wrapper = mount(ViewEntry, {props});
    await flushPromises();
    return wrapper;
  }

  it('should show form', async () => {
    const wrapper = await setUp();
    const input = wrapper.find<HTMLInputElement>('input[type=text]');
    expect(input.exists()).toBe(true);
    expect(input.element.value).toBe('test document');

    const displayedExtension = wrapper.find('.input-group-addon');
    expect(displayedExtension.exists()).toBe(true);
    expect(displayedExtension.element.textContent).toContain('.odt');
  });

  it('should update name without error', async () => {
    const wrapper = await setUp();
    fetchMock.post('/change-metadata/dummytoken', {detail: "ok"});
    await wrapper.find<HTMLInputElement>('input[type=text]').setValue('new name');
    await wrapper.find('.input-group-btn button').trigger('click');
    await flushPromises();
    expect(wrapper.get('.media-heading i').classes()).toContain('fa-check');
  });

  it('should show http error on save', async () => {
    const wrapper = await setUp();
    fetchMock.post('/change-metadata/dummytoken', 400);
    await wrapper.find<HTMLInputElement>('input[type=text]').setValue('new name');
    await wrapper.find('.input-group-btn button').trigger('click');
    await flushPromises();
    expect(wrapper.get('.text-danger').text()).toBe("error");
    expect(wrapper.find('.media-right > .btn.btn-danger').exists()).toBe(true);
  });


  describe('should have a valid name and extension depending of the full filename', () => {
    test('if the fullname is empty', async () => {
      const wrapper = await setUp({name: ''});
      expect(wrapper.find<HTMLInputElement>('input[type=text]').element.value).toBe('');
      expect(wrapper.find('.input-group-addon').exists()).toBe(false);
    });

    test('if the fullname has no dot', async () => {
      const wrapper = await setUp({name: 'my_file'});
      expect(wrapper.find<HTMLInputElement>('input[type=text]').element.value).toBe('my_file');
      expect(wrapper.find('.input-group-addon').exists()).toBe(false);
    });

    test('if the fullname has no extension', async () => {
      const wrapper = await setUp({name: 'my_file.'});
      expect(wrapper.find<HTMLInputElement>('input[type=text]').element.value).toBe('my_file.');
      expect(wrapper.find('.input-group-addon').exists()).toBe(false);
    });

    test('if the fullname has a name and an extension, separated by a dot', async () => {
      const wrapper = await setUp({name: 'my_file.txt'});
      expect(wrapper.find<HTMLInputElement>('input[type=text]').element.value).toBe('my_file');
      expect(wrapper.find('.input-group-addon').element.textContent).toBe('.txt');
    });

    test('if the fullname has a name (containing a dot) and an extension, separated by a dot', async () => {
      const wrapper = await setUp({name: 'my.file.txt'});
      expect(wrapper.find<HTMLInputElement>('input[type=text]').element.value).toBe('my.file');
      expect(wrapper.find('.input-group-addon').element.textContent).toBe('.txt');
    });
  });
});

test('file can be deleted', async () => {
  fetchMock.restore().get('/metadata/dummytoken', documentMetadata);
  const wrapper = mount(ViewEntry, {props});
  await flushPromises();
  await wrapper.get('.btn-danger').trigger('click');
  expect(wrapper.emitted()).toHaveProperty('delete');
});

test('image can be rotated (bubble up updated token)', async () => {
  fetchMock.restore().get('/metadata/dummy:token', {
    mimetype: 'image/jpeg',
    size: 82381,
    url: './placeholder.jpeg',
    name: 'test document.jpeg',
  });
  const wrapper = shallowMount(ViewEntry, {props: {...props, value: 'dummy:token'}});
  await flushPromises();
  wrapper.getComponent(ViewingModal).vm.$emit('updateToken', 'newtoken');
  await nextTick();
  expect(wrapper.findComponent({name: 'ViewingModal'}).attributes('id')).toBe('dummy-token');
  expect(wrapper.emitted()).toHaveProperty('updateToken');
});
