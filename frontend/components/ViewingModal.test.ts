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
import ViewingModal from './ViewingModal.vue';
import {describe, expect, it, vi} from "vitest";
import fetchMock from "fetch-mock";


let modalOpened: CallableFunction;
const on = vi.fn((eventName, handler: CallableFunction) => {
  modalOpened = handler;
});
const modalFn = vi.fn();
const jQueryMock = vi.fn(() => ({
  modal: modalFn,
  on: on,
}));

vi.stubGlobal('jQuery', jQueryMock);

const props = {
  id: '0',
  baseUrl: '/',
  value: 'foobar',
  file: {
    mimetype: 'image/jpeg',
    size: 38329,
    url: './placeholder.jpeg',
    name: 'test image',
  },
};


describe('modal with small image', () => {
  const wrapper = mount(ViewingModal, {props});

  // // Mock modal dimensions
  const modal = wrapper.find('.modal-body');
  vi.spyOn(modal.element, 'clientWidth', 'get').mockImplementation(() => 800);

  it('should mount', () => {
    expect(wrapper.text()).toContain('test image');
    expect(modalOpened).toBeTruthy();
    expect(buttonSave.attributes()).toHaveProperty('disabled');
  });

  const buttonRotateLeft = wrapper.find('.text-left button.btn-default:first-child');
  const buttonRotateRight = wrapper.find('.text-left button.btn-default:nth-child(2)');
  const buttonSave = wrapper.find('.text-left button:last-child');
  const spyImgLoaded = vi.spyOn(wrapper.vm, 'imageLoaded');

  // Mock image size
  const img = wrapper.find('img');
  const clientWidth = vi.spyOn(img.element, 'clientWidth', 'get').mockImplementation(() => 500);
  const clientHeigth = vi.spyOn(img.element, 'clientHeight', 'get').mockImplementation(() => 300);

  it('should update according to image dimensions when modal opened', async () => {
    await modalOpened();
    await flushPromises();
    expect(spyImgLoaded).toHaveBeenCalled();
    expect(clientWidth).toHaveBeenCalled();
    expect(clientHeigth).toHaveBeenCalled();
    expect(modal.attributes('style')).toContain('height: 330px');
  });

  it('should not call imageLoaded twice', async () => {
    await img.trigger('load');
    expect(spyImgLoaded).toHaveBeenCalled();
    spyImgLoaded.mockClear();
    await modalOpened();
    expect(spyImgLoaded).not.toHaveBeenCalled();
    expect(modal.attributes('style')).toContain('height: 330px');
  });

  it('should rotate -90deg landscape image, updating style', async () => {
    await buttonRotateLeft.trigger('click');
    expect(img.attributes('style')).toContain('transform: rotate(-90deg) translate(-50%, -50%);');
    expect(buttonSave.attributes('disabled')).toBeFalsy();
    expect(modal.attributes('style')).toContain('height: 530px');
  });

  it('should rotate -180deg, updating style', async () => {
    await buttonRotateLeft.trigger('click');
    expect(img.attributes('style')).toContain('transform: rotate(-180deg) translate(0, -100%);');
    expect(modal.attributes('style')).toContain('height: 330px');
  });

  it('should rotate 90deg, updating style', async () => {
    await buttonRotateRight.trigger('click');
    await buttonRotateRight.trigger('click');
    await buttonRotateRight.trigger('click');
    expect(img.attributes('style')).toContain('transform: rotate(90deg) translate(50%, -50%);');
    expect(modal.attributes('style')).toContain('height: 530px');
    await buttonRotateLeft.trigger('click');
  });

  it('should rotate -90deg portrait image, updating style', async () => {
    await wrapper.setData({originalHeight: 900});
    await buttonRotateLeft.trigger('click');
    await buttonRotateLeft.trigger('click');
    expect(img.attributes('style')).toContain('transform: rotate(-180deg) translate(0, -100%);');
    expect(modal.attributes('style')).toContain('height: 930px');
  });
  describe("rotation api", () => {
    it('should not save rotation with http error', async () => {
      fetchMock.reset().post('/rotate-image/foobar', 400);
      await buttonSave.trigger('click');
      await flushPromises();

      expect(wrapper.emitted('updateToken')).toBeFalsy();
      expect(wrapper.find('.text-danger').exists()).toBe(true);
    });

    it('should not save rotation with other error', async () => {
      fetchMock.reset().post('/rotate-image/foobar', {throws: new Error('Any error')});
      await buttonSave.trigger('click');
      await flushPromises();

      expect(wrapper.emitted('updateToken')).toBeFalsy();
      expect(wrapper.find('.text-danger').exists()).toBe(true);
    });

    it('should save rotation', async () => {
      fetchMock.reset().post('/rotate-image/foobar', {
        token: 'new-token',
      });
      await buttonSave.trigger('click');
      await flushPromises();
      expect(wrapper.emitted('updateToken')).toBeTruthy();
    });
  });

  it('should destroy closing modal', () => {
    wrapper.unmount();
    expect(modalFn).toHaveBeenCalledWith('hide');
  });
});

it('should open on mount if needed', () => {
  mount(ViewingModal, {
    props: {
      ...props,
      openOnMount: true,
    },
  });
  expect(modalFn).toHaveBeenCalledWith('show');
});

it('should mount modal without image', () => {
  const wrapper = mount(ViewingModal, {
    props: {
      ...props,
      file: {
        mimetype: 'application/pdf',
        size: 38329,
        url: './placeholder.pdf',
        name: 'test document',
      },
    },
  });
  expect(wrapper.find('img').exists()).toBe(false);
});
