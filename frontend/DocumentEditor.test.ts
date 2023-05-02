/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */

import {flushPromises, shallowMount} from '@vue/test-utils';
import {beforeEach, expect, it, vi} from "vitest";
import DocumentEditor from './DocumentEditor.vue';
import fetchMock from "fetch-mock";
import {getDocument} from "pdfjs-dist";
import type {PDFDocumentProxy} from "pdfjs-dist";
import ToolbarPagination from "./components/ToolbarPagination.vue";
import {nextTick} from "vue";
import {PDFViewer} from "pdfjs-dist/web/pdf_viewer";
import ToolbarRotation from "./components/ToolbarRotation.vue";
import ToolbarZoom from "./components/ToolbarZoom.vue";
import ToolbarAnnotation from "./components/ToolbarAnnotation.vue";

const props = {
  baseUrl: '/',
  value: 'foo',
};
const pdfDocument = {
  annotationStorage: {
    size: 0,
  },
  numPages: 2,
  saveDocument: vi.fn(),
};

vi.mock('pdfjs-dist', async () => {
  const mod = await vi.importActual<typeof import('pdfjs-dist')>('pdfjs-dist');
  return {
    ...mod,
    getDocument: vi.fn(() => ({
      promise: Promise.resolve(pdfDocument),
    })),
  };
});

vi.mock('pdfjs-dist/web/pdf_viewer', async () => {
  const mod = await vi.importActual<typeof import('pdfjs-dist/web/pdf_viewer')>('pdfjs-dist/web/pdf_viewer');
  const currentScale = 1;
  let currentPageNumber = 1;
  const eventBus = new mod.EventBus();
  return {
    ...mod,
    PDFViewer: vi.fn(() => ({
          setDocument: vi.fn(),
          getPageView: vi.fn(() => ({update: vi.fn()})),
          // Mock zoom
          currentScale: currentScale,
          currentScaleValue: 'auto',
          increaseScale: function ({scaleFactor}: { scaleFactor: number }) {
            this.currentScale = this.currentScale * scaleFactor;
          },
          decreaseScale: function ({scaleFactor}: { scaleFactor: number }) {
            this.currentScale = this.currentScale / scaleFactor;
          },
          // Mock pagination
          set currentPageNumber(pageNumber: number) {
            currentPageNumber = pageNumber;
            eventBus.dispatch('pagechanging', {pageNumber});
          },
          get currentPageNumber() {
            return currentPageNumber;
          },
          eventBus: eventBus,
        }),
    ),
  };
});

beforeEach(() => {
  fetchMock.reset()
      .get('/metadata/foo', {url: 'foo.pdf'})
  ;
});

it('should mount', async () => {
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  expect(getDocument).toHaveBeenCalledWith('foo.pdf');
  expect(wrapper.find('.text-danger').exists()).not.toBe(true);
  expect(wrapper.vm.$data).toHaveProperty('highlightingColor', '');
  expect(wrapper.vm.$data).toHaveProperty('commentingColor', '');
  expect(wrapper.vm.$data).toHaveProperty('viewer.currentPageNumber', 1);

  (wrapper.vm.$data.viewer as PDFViewer).eventBus.dispatch('pagesinit', {});
  expect(wrapper.vm.$data).toHaveProperty('viewer.currentScaleValue', 'auto');
  expect(wrapper.vm.$data).toHaveProperty('currentZoom', 'auto');
});

it('should display fetching error', async () => {
  fetchMock.reset().get('/metadata/foo', {throws: new Error('not found')});
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  expect(wrapper.text()).toContain('not found');
});

it('should display rendering error', async () => {
  vi.mocked(getDocument).mockImplementationOnce(() => {
    throw new Error('rendering error');
  });
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  expect(wrapper.text()).toContain('rendering error');
});

it('should not display file infected', async () => {
  vi.mocked(getDocument).mockClear();
  const wrapper = shallowMount(DocumentEditor, {
    props: {
      baseUrl: '/',
      value: 'FileInfectedException',
    },
  });
  await flushPromises();
  expect(wrapper.text()).toContain('view_entry.file_infected');
  expect(getDocument).not.toHaveBeenCalled();
});

it('should change current page', async () => {
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  expect(wrapper.getComponent(ToolbarPagination).props().currentPage).toBe(1);
  expect(wrapper.getComponent(ToolbarPagination).props().pages).toBe(2);

  // Click
  wrapper.getComponent(ToolbarPagination).vm.$emit('onChangeCurrentPage', 2);
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('viewer.currentPageNumber', 2);
  expect(wrapper.getComponent(ToolbarPagination).props().currentPage).toBe(2);

  // Manual scrolling
  (wrapper.vm.$data.viewer as PDFViewer).eventBus.dispatch('pagechanging', {pageNumber: 1});
  await nextTick();
  expect(wrapper.getComponent(ToolbarPagination).props().currentPage).toBe(1);
});

it('should rotate current page', async () => {
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  expect(wrapper.vm.$data).toHaveProperty('rotations', {});
  wrapper.getComponent(ToolbarRotation).vm.$emit('onRotate', 90);
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('rotations.0', 90);

  // Cancel rotation
  wrapper.getComponent(ToolbarRotation).vm.$emit('onRotate', 0);
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('rotations', {});
});

it('should apply zoom', async () => {
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  (wrapper.vm.$data.viewer as PDFViewer).eventBus.dispatch('pagesinit', {});
  await nextTick();

  wrapper.getComponent(ToolbarZoom).vm.$emit('onZoomIn');
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('currentZoom', '1.1');

  wrapper.getComponent(ToolbarZoom).vm.$emit('onZoomOut');
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('currentZoom', '1');

  wrapper.getComponent(ToolbarZoom).vm.$emit('onSetScale', 'page-width');
  await nextTick();
  expect(wrapper.vm.$data).toHaveProperty('currentZoom', 'page-width');
});

it('should handle hightlighting', async () => {
  vi.useFakeTimers();

  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  const highlighter = wrapper.findAllComponents(ToolbarAnnotation)[0];
  expect(highlighter.props().isActivated).toBe(false);
  expect(vi.getTimerCount()).toBe(0);

  highlighter.vm.$emit('onChange', '#ff0000');
  await nextTick();
  expect(highlighter.props().isActivated).toBe(true);
  expect(vi.getTimerCount()).toBe(1);

  // @ts-ignore just to test hasAnnotation
  (wrapper.vm.$data.pdfDocument as PDFDocumentProxy).annotationStorage.size = 1;
  vi.advanceTimersToNextTimer();
  await nextTick();
  expect(wrapper.find('button').classes()).toContain('btn-primary');

  highlighter.vm.$emit('onChange', '');
  await nextTick();
  expect(vi.getTimerCount()).toBe(0);
});

it('should switch from hightlighting to commenting', async () => {
  vi.useFakeTimers();

  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  const highlighter = wrapper.findAllComponents(ToolbarAnnotation)[0];
  const commenter = wrapper.findAllComponents(ToolbarAnnotation)[1];
  expect(highlighter.props().isActivated).toBe(false);
  expect(commenter.props().isActivated).toBe(false);
  expect(vi.getTimerCount()).toBe(0);

  highlighter.vm.$emit('onChange', '#ff0000');
  await nextTick();
  expect(highlighter.props().isActivated).toBe(true);
  expect(commenter.props().isActivated).toBe(false);
  expect(vi.getTimerCount()).toBe(1);

  commenter.vm.$emit('onChange', '#ff0000');
  await nextTick();
  expect(highlighter.props().isActivated).toBe(false);
  expect(commenter.props().isActivated).toBe(true);
  expect(vi.getTimerCount()).toBe(1);

  commenter.vm.$emit('onChange', '');
  await nextTick();
  expect(vi.getTimerCount()).toBe(0);
});

it('should destroy removing timers', async () => {
  vi.useFakeTimers();

  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  const highlighter = wrapper.findAllComponents(ToolbarAnnotation)[0];
  highlighter.vm.$emit('onChange', '#ff0000');
  await nextTick();
  expect(highlighter.props().isActivated).toBe(true);
  expect(vi.getTimerCount()).toBe(1);

  wrapper.unmount();
  expect(vi.getTimerCount()).toBe(0);
});

it('should not save to API, if nothing to save', async () => {
  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  await wrapper.find('button').trigger('click');
  await flushPromises();

  expect(fetchMock.called('/save-editor/foo')).toBeFalsy();
});

it('should save to API, refreshing token', async () => {
  vi.useFakeTimers();
  fetchMock
      .postOnce('/save-editor/foo', {token: "new-token"})
      .get('/metadata/new-token', {url: 'foo.pdf'})
  ;

  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  vi.mocked(getDocument).mockClear();
  wrapper.getComponent(ToolbarRotation).vm.$emit('onRotate', 90);
  await nextTick();
  await wrapper.find('button').trigger('click');
  await flushPromises();

  expect(fetchMock.called('/save-editor/foo')).toBeTruthy();
  expect(getDocument).toHaveBeenCalledWith('foo.pdf');
  expect(wrapper.find('.text-danger').exists()).not.toBe(true);
});

it('should handle API errors saving', async () => {
  fetchMock.resetHistory().postOnce('/save-editor/foo', {throws: new Error('not found')});

  const wrapper = shallowMount(DocumentEditor, {props});
  await flushPromises();
  wrapper.getComponent(ToolbarRotation).vm.$emit('onRotate', 90);
  await nextTick();
  await wrapper.find('button').trigger('click');
  await flushPromises();

  expect(fetchMock.called('/save-editor/foo')).toBeTruthy();
  expect(wrapper.find('.text-danger').exists()).toBe(true);
  expect(wrapper.text()).toContain('not found');
});

it('should be usable without toolbar', async () => {
  fetchMock
      .postOnce('/save-editor/foo', {token: "new-token"})
      .get('/metadata/new-token', {url: 'foo.pdf'})
  ;
  const wrapper = shallowMount(DocumentEditor, {
    props: {
      ...props,
      pagination: false,
      zoom: false,
      rotation: false,
      highlight: false,
      comment: false,
    },
  });
  await flushPromises();
  expect(getDocument).toHaveBeenCalledWith('foo.pdf');
  expect(wrapper.find('.text-danger').exists()).not.toBe(true);

  // fire custom events to control the element externally
  wrapper.element.dispatchEvent(new CustomEvent<number>('rotate', {detail: 90}));
  await nextTick();
  expect(wrapper.find('button').classes()).toContain('btn-primary');

  wrapper.element.dispatchEvent(new CustomEvent<number>('save'));
  await nextTick();
  expect(fetchMock.called('/save-editor/foo')).toBeTruthy();
});
