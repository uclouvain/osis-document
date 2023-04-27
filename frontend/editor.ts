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
// eslint-disable-next-line vue/prefer-import-from-vue
import {createApp} from '@vue/runtime-dom'; // So it can be spied on in tests
import {i18n} from './i18n';
import Editor from './DocumentEditor.vue';


interface EditorProps extends Record<string, unknown> {
  baseUrl: string,
  value: string,
  pagination?: boolean,
  zoom?: boolean,
  comment?: boolean,
  highlight?: boolean,
  rotation?: boolean,
}

function initEditors() {
  document.querySelectorAll<HTMLElement>('.osis-document-editor:not([data-v-app])').forEach((elem) => {
    const props: EditorProps = {baseUrl: "", value: "", ...elem.dataset};
    for (const propName of ['pagination', 'zoom', 'comment', 'highlight', 'rotation'])
      if (typeof elem.dataset[propName] !== 'undefined') {
        props[propName] = elem.dataset[propName] === "true";
      }
    createApp(Editor, props).use(i18n).mount(elem);
  });
}

// Initialize at first load
initEditors();

// Initialize later if nodes are added dynamically
const observer = new MutationObserver(initEditors);
observer.observe(document, {childList: true, subtree: true});
