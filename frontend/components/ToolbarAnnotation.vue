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
  <div class="btn-group dropup annotation-dropdown">
    <button
        class="btn"
        type="button"
        :class="isActivated ? 'btn-primary': 'btn-default'"
        @click="$emit( 'onChange', isActivated ? '': color || Object.values(colors)[0] )"
    >
      <span
          class="fas"
          :class="icon"
      />
    </button>
    <button
        type="button"
        class="btn btn-default dropdown-toggle"
        data-toggle="dropdown"
        data-bs-toggle="dropdown"
    >
      <span class="caret" />
    </button>
    <ul class="dropdown-menu">
      <li
          v-for="(rgb, color_name) in colors"
          :key="color_name"
          :class="`${classPrefix}-${color_name}`"
      >
        <a
            href="#"
            :class="`${classPrefix}-${color_name}`"
            @click.prevent="$emit('onChange', rgb)"
        >
          {{ $t(`editor.colors.${color_name}`) }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isActivated: boolean,
  color: string,
  classPrefix: string,
  icon: string,
  colors: Record<string, string>,
}>();
defineEmits<{
  (e: 'onChange', color: string): void,
}>();
</script>

<style lang="scss">
.annotation-dropdown .dropdown-menu > li > a {
  color: inherit;
}
</style>
