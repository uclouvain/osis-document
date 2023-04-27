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
        :class="{'disabled': currentPage == 1}"
        @click="currentPage != 1 && $emit('onChangeCurrentPage', currentPage - 1)"
    >
      <span class="fas fa-angle-up" />
    </button>
    <a
        class="btn btn-default disabled"
        role="button"
    >
      {{ $t('editor.pagination', {currentPage, pages}) }}
    </a>
    <button
        class="btn btn-default"
        type="button"
        :class="{'disabled': currentPage == pages}"
        @click="currentPage != pages && $emit('onChangeCurrentPage', currentPage + 1)"
    >
      <span class="fas fa-angle-down" />
    </button>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  currentPage: number,
  pages: number,
}>();

defineEmits<{
  (e: 'onChangeCurrentPage', page: number): void
}>();
</script>
