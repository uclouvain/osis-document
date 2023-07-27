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

import {expect, test, vi} from 'vitest';
/* eslint-disable vue/prefer-import-from-vue */
import * as exports from '@vue/runtime-dom';
import {createApp} from "vue";

const visualizer = vi.fn();
vi.mock('./DocumentVisualizer.vue', () => ({
  default: visualizer,
}));
const uploader = vi.fn();
vi.mock('./DocumentUploader.vue', () => ({
  default: uploader,
}));

const spy = vi.spyOn(exports, 'createApp').mockImplementation(createApp);

test('mount simple visualizer', async () => {
  document.body.innerHTML = `<div class="osis-document-visualizer"
    data-base-url="/api"
    data-values="foo,bar"
    data-post-process-status="DONE"
    data-get-progress-url="get-progress-async-post-processing/UUID"
    data-base-uuid="UUID"
    data-wanted-post-process=""
  ></div>`;

  // Executes main file
  await import('./main');

  expect(spy).toBeCalledTimes(1);
  expect(spy).toHaveBeenCalledWith(visualizer, {
    baseUrl: '/api',
    values: ['foo', 'bar'],
    postProcessStatus: 'DONE',
    getProgressUrl: 'get-progress-async-post-processing/UUID',
    baseUuid: 'UUID',
    wantedPostProcess: '',
  });
});

test('mount visualizer without values', async () => {
  spy.mockClear();
  document.body.innerHTML = `<div class="osis-document-visualizer" data-base-url="/api"></div>`;

  // Executes main file
  await import('./main');

  expect(spy).toBeCalledTimes(1);
  expect(spy).toHaveBeenCalledWith(visualizer, {
    baseUrl: '/api',
    values: [],
    postProcessStatus: '',
    getProgressUrl: '',
    baseUuid: '',
    wantedPostProcess: '',
  });
});

test('mount simple uploader', async () => {
  spy.mockClear();
  document.body.innerHTML = `<div class="osis-document-uploader" data-base-url="/api"></div>`;

  // Executes main file
  await import('./main');

  expect(spy).toBeCalledTimes(1);
  expect(spy).toHaveBeenCalledWith(uploader, {
    baseUrl: '/api',
  });
});

test('mount uploader with conversions', async () => {
  spy.mockClear();
  document.body.innerHTML = `<div class="osis-document-uploader"
    data-base-url="/api"
    data-values="foo,bar"
    data-max-size="1024"
    data-min-files="2"
    data-max-files="3"
    data-mimetypes="image/png,image/jpeg"
    data-automatic-upload="false"
    data-editable-filename="false"
  ></div>`;

  // Executes main file
  await import('./main');

  expect(spy).toBeCalledTimes(1);
  expect(spy).toHaveBeenCalledWith(uploader, {
    baseUrl: '/api',
    values: ['foo', 'bar'],
    maxSize: 1024,
    minFiles: 2,
    maxFiles: 3,
    mimetypes: ['image/png', 'image/jpeg'],
    automaticUpload: false,
    editableFilename: false,
  });
});

