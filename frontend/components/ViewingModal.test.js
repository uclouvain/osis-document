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
import ViewingModal from './ViewingModal.vue';
import fetchMock from 'fetch-mock';

describe('modal with small image', () => {
  let eventCallback;
  window.jQuery = jest.fn(() => ({
    modal: () => {},
    on: (e, cb) => {eventCallback = cb;},
  }));

  const wrapper = mount(ViewingModal, {
    propsData: {
      file: {
        mimetype: 'image/jpeg',
        size: 38329,
        url: './placeholder.jpeg',
        name: 'test image',
      },
      id: '0',
      baseUrl: '/',
      value: 'foobar',
    },
    mocks: {
      jQuery,
      $t: k => k,
    },
  });

  // Mock modal dimensions
  wrapper.vm.$refs.modal = { clientWidth: 800 };

  it('should mount', () => {
    expect(wrapper.text()).toContain('test image');
    expect(eventCallback).toBeTruthy();
    expect(buttonSave.attributes('disabled')).toBeTruthy();
  });

  const buttonRotateLeft = wrapper.find('.text-left button.btn-default:first-child');
  const buttonRotateRight = wrapper.find('.text-left button.btn-default:nth-child(2)');
  const buttonSave = wrapper.find('.text-left button:last-child');
  const img = wrapper.find('img');
  const spyImgLoaded = jest.spyOn(wrapper.vm, 'imageLoaded');

  it('should call image loaded when modal is loaded', async () => {
    eventCallback();
    expect(spyImgLoaded).toHaveBeenCalled();
  });

  describe('landscape', () => {
    it('should update image dimensions', async () => {
      wrapper.vm.imageLoaded({
        clientWidth: 500,
        clientHeight: 300,
      });
      await wrapper.vm.$nextTick();
      spyImgLoaded.mockReset();
      eventCallback();
      expect(spyImgLoaded).not.toHaveBeenCalled();
      expect(wrapper.vm.modalHeight).toBe('330px');
    });

    it('should rotate -90deg, updating style', async () => {
      await buttonRotateLeft.trigger('click');
      expect(wrapper.vm.rotation).toBe(-90);
      expect(img.attributes('style')).toContain('transform: rotate(-90deg) translate(-50%, -50%);');
      expect(buttonSave.attributes('disabled')).toBeFalsy();
      expect(wrapper.vm.modalHeight).toBe('530px');
    });

    it('should rotate -180deg, updating style', async () => {
      await buttonRotateLeft.trigger('click');
      expect(wrapper.vm.rotation).toBe(-180);
      expect(img.attributes('style')).toContain('transform: rotate(-180deg) translate(0, -100%);');
      expect(wrapper.vm.modalHeight).toBe('330px');
    });

    it('should rotate 90deg, updating style', async () => {
      await buttonRotateRight.trigger('click');
      await buttonRotateRight.trigger('click');
      await buttonRotateRight.trigger('click');
      expect(wrapper.vm.rotation).toBe(90);
      expect(img.attributes('style')).toContain('transform: rotate(90deg) translate(50%, -50%);');
      expect(wrapper.vm.modalHeight).toBe('530px');
      await buttonRotateLeft.trigger('click');
    });
  });

  describe('tall portrait', () => {
    it('should rotate -90deg, updating style', async () => {
      wrapper.setData({ originalHeight: 900 });
      await buttonRotateLeft.trigger('click');
      await buttonRotateLeft.trigger('click');
      expect(wrapper.vm.rotation).toBe(-180);
      expect(wrapper.vm.modalHeight).toBe('930px');
    });
  });

  it('should not save rotation with http error', async () => {
    fetchMock.post('/rotate-image/foobar', 400);
    await buttonSave.trigger('click');
    await wrapper.vm.$nextTick();
    expect(wrapper.emitted('update-token')).toBeFalsy();
    expect(wrapper.vm.error).toBeTruthy();
  });

  it('should not save rotation with other error', async () => {
    fetchMock.restore().post('/rotate-image/foobar', { throws: new Error('Any error') });
    await buttonSave.trigger('click');
    await wrapper.vm.$nextTick();
    expect(wrapper.emitted('update-token')).toBeFalsy();
    expect(wrapper.vm.error).toBeTruthy();
  });

  it('should save rotation', async () => {
    fetchMock.restore().post('/rotate-image/foobar', {
      token: 'new-token',
    });
    await buttonSave.trigger('click');
    await wrapper.vm.$nextTick(); // wait for request
    await wrapper.vm.$nextTick(); // wait for re--rendering
    expect(wrapper.emitted('update-token')).toBeTruthy();
  });

  it('should destroy closing modal', () => {
    wrapper.destroy();
    expect(window.jQuery).toHaveBeenCalled();
  });

  fetchMock.restore();
});

describe('modal without image', () => {
  window.jQuery = jest.fn(() => ({
    modal: () => {},
    on: (e, cb) => {cb();},
  }));

  const wrapper = mount(ViewingModal, {
    propsData: {
      file: {
        mimetype: 'application/pdf',
        size: 38329,
        url: './placeholder.pdf',
        name: 'test document',
      },
      id: '0',
      baseUrl: '/',
      value: 'foobar',
    },
    mocks: {
      jQuery,
      $t: k => k,
    },
  });

  it('should mount', () => {
    expect(wrapper.vm.isImage).toBe(false);
  });
});
