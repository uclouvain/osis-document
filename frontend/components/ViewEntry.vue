<!--
  -
  -   OSIS stands for Open Student Information System. It's an application
  -   designed to manage the core business of higher education institutions,
  -   such as universities, faculties, institutes and professional schools.
  -   The core business involves the administration of students, teachers,
  -   courses, programs and so on.
  -
  -   Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
  -
  -   This program is free software: you can redistribute it and/or modify
  -   it under the terms of the GNU General Public License as published by
  -   the Free Software Foundation, either version 3 of the License, or
  -   (at your option) any later version.
  -
  -   This program is distributed in the hope that it will be useful,
  -   but WITHOUT ANY WARRANTY; without even the implied warranty of
  -   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  -   GNU General Public License for more details.
  -
  -   A copy of this license - GNU General Public License - is available
  -   at the root of the source code of this program.  If not,
  -   see http://www.gnu.org/licenses/.
  -
  -->

<template>
  <li class="media">
    <div
        v-if="isImage"
        class="media-left"
    >
      <img
          class="media-object img-thumbnail"
          :src="file.url"
          :alt="file.name"
          width="80"
      >
    </div>
    <div class="media-body">
      <div
          v-if="loading"
          class="progress"
      >
        <div
            class="progress-bar progress-bar-striped active"
            role="progressbar"
            aria-valuenow="0"
            aria-valuemin="0"
            aria-valuemax="100"
            :style="{width: `100%`}"
        >
          <span class="sr-only">{{ $t('view_entry.loading') }}</span>
        </div>
      </div>
      <span
          v-else-if="error"
          class="text-danger"
      >
        {{ $t('error', { error }) }}
      </span>
      <h4
          v-else
          class="media-heading"
      >
        {{ file.name }}
        <small><span class="text-nowrap">{{ humanizedSize }}</span> ({{ file.mimetype }})</small>
      </h4>
    </div>
    <div
        v-if="file"
        class="media-right text-right"
        style="min-width: 7em"
    >
      <div class="btn-group">
        <a
            class="btn btn-info"
            v-bind="isViewableDocument ? {
              'data-toggle': 'modal',
              'data-target': `#modal-${id}`,
            } : {
              target: '_blank',
              href: file.url,
            }"
        >
          <span class="glyphicon glyphicon-eye-open" />
        </a>
        <button
            class="btn btn-danger"
            @click="$emit('delete')"
        >
          <span class="glyphicon glyphicon-trash" />
        </button>
      </div>
    </div>
    <ViewingModal
        v-if="isViewableDocument"
        :id="id"
        :file="file"
    />
  </li>
</template>

<script>
/**
 * This component's goal is to view an uploaded file and edit it
 */
import { humanizedSize } from '../utils';
import ViewingModal from './ViewingModal';

export default {
  name: 'ViewEntry',
  components: { ViewingModal },
  props: {
    value: {
      type: String,
      required: true,
    },
    id: {
      type: String,
      required: true,
    },
    baseUrl: {
      type: String,
      required: true,
    },
  },
  data () {
    return {
      file: null,
      loading: true,
      error: '',
    };
  },
  computed: {
    isImage: function () {
      return !!this.file && this.file.mimetype.split('/')[0] === 'image';
    },
    isViewableDocument: function () {
      if (!this.file) {
        return false;
      }
      const mimetype = this.file.mimetype;
      return mimetype.split('/')[0] === 'image' || mimetype === 'application/pdf';
    },
    humanizedSize: function () {
      return humanizedSize(this.file.size);
    },
  },
  mounted () {
    this.getFile();
  },
  methods: {
    getFile: async function () {
      try {
        const response = await fetch(`${this.baseUrl}metadata/${this.value}`);
        if (response.status === 200) {
          this.file = await response.json();
        } else {
          this.error = response.statusText;
        }
      } catch (e) {
        this.error = e;
      }
      this.loading = false;
    },
  },
};
</script>

<style lang="scss">

</style>