<!--
  -
  - OSIS stands for Open Student Information System. It's an application
  - designed to manage the core business of higher education institutions,
  - such as universities, faculties, institutes and professional schools.
  - The core business involves the administration of students, teachers,
  - courses, programs and so on.
  -
  - Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
  -
  - This program is free software: you can redistribute it and/or modify
  - it under the terms of the GNU General Public License as published by
  - the Free Software Foundation, either version 3 of the License, or
  - (at your option) any later version.
  -
  - This program is distributed in the hope that it will be useful,
  - but WITHOUT ANY WARRANTY; without even the implied warranty of
  - MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  - GNU General Public License for more details.
  -
  - A copy of this license - GNU General Public License - is available
  - at the root of the source code of this program.  If not,
  - see http://www.gnu.org/licenses/.
  -
  -->

<template>
  <div class="btn-group">
    <button
        class="btn btn-default"
        type="button"
        @click="$emit('onZoomOut')"
    >
      <span class="fas fa-magnifying-glass-minus" />
    </button>
    <div
        class="btn-group dropup"
        role="group"
    >
      <button
          type="button"
          class="btn btn-default dropdown-toggle"
          data-toggle="dropdown"
          data-bs-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
      >
        {{ zoomTitle(currentZoom) }}
        <span class="caret" />
      </button>
      <ul class="dropdown-menu">
        <li
            v-for="scale in scales"
            :key="scale"
            :value="scale"
            :class="currentZoom == scale ? 'active' : ''"
        >
          <a
              href="#"
              @click.prevent="$emit('onSetScale', scale)"
          >
            {{ zoomTitle(scale) }}
          </a>
        </li>
      </ul>
    </div>
    <button
        class="btn btn-default"
        type="button"
        @click="$emit('onZoomIn')"
    >
      <span class="fas fa-magnifying-glass-plus" />
    </button>
  </div>
</template>

<script lang="ts" setup>
import {useI18n} from 'vue-i18n';

const {t} = useI18n();

defineProps<{
  currentZoom: string,
}>();

defineEmits<{
  (e: 'onZoomIn'): void,
  (e: 'onZoomOut'): void,
  (e: 'onSetScale', scale: string): void,
}>();

const scales = [
  "auto",
  "page-actual",
  "page-fit",
  "page-width",
  "0.5",
  "0.75",
  "1",
  "1.25",
  "1.5",
  "2",
  "3",
  "4",
];

function zoomTitle(scale: string): string {
  return !isNaN(parseFloat(scale)) ? `${Math.ceil(parseFloat(scale) * 100)}%` : t(`editor.zoom.${scale}`);
}
</script>
