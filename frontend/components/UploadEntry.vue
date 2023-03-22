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
          :src="fileUrl"
          :alt="file.name"
          width="80"
          @load="revokeUrl(fileUrl)"
      >
    </div>
    <div class="media-body">
      <h4 class="media-heading">
        {{ file.name }}
        <small><span class="text-nowrap">{{ humanizedSize }}</span> ({{ file.type }})</small>
      </h4>
      <div
          v-if="!error"
          class="progress"
      >
        <div
            class="progress-bar progress-bar-striped active"
            role="progressbar"
            :aria-valuenow="progress"
            aria-valuemin="0"
            aria-valuemax="100"
            :style="{width: `${progress}%`}"
        >
          <span class="sr-only">{{ $t('upload_entry.completion', { progress }) }}</span>
        </div>
      </div>
      <span
          v-else
          class="text-danger"
      >
        {{ error }}
      </span>
    </div>
    <div class="media-right">
      <button
          type="button"
          class="btn btn-danger"
          @click="$emit('delete')"
      >
        <span class="fas fa-trash-alt" />
      </button>
    </div>
  </li>
</template>

<script lang="ts">
/**
 * This component goal is to upload a local file and emit a token
 */
import {humanizedSize} from '../utils';
import EventBus from '../event-bus';
import {defineComponent} from 'vue';
import type {ErrorReponse, TokenReponse} from "../interfaces";

export default defineComponent({
  name: 'UploadEntry',
  props: {
    file: {
      type: File,
      required: true,
    },
    baseUrl: {
      type: String,
      required: true,
    },
    maxSize: {
      type: Number,
      default: 0,
    },
    mimetypes: {
      type: Array,
      default: () => [],
    },
    automatic: {
      type: Boolean,
      default: true,
    },
  },
  emits: {
    setToken(token: string) {
      return token.length > 0;
    },
    delete() {
      return true;
    },
  },
  data() {
    return {
      progress: 0,
      token: '',
      error: '',
    };
  },
  computed: {
    isImage: function () {
      return this.file.type.split('/')[0] === 'image';
    },
    fileUrl: function () {
      return URL.createObjectURL(this.file);
    },
    humanizedSize: function () {
      return humanizedSize(this.file.size);
    },
  },
  mounted() {
    if (this.maxSize && this.file.size > this.maxSize) {
      this.error = this.$t('upload_entry.too_large');
    } else if (this.mimetypes.length && !this.mimetypes.includes(this.file.type)) {
      this.error = this.$tc('upload_entry.wrong_type', this.mimetypes.length, {types: this.mimetypes.join(', ')});
    } else if (this.automatic) {
      this.sendFile();
    } else {
      EventBus.on('upload', this.sendFile);
    }
  },
  methods: {
    revokeUrl: function (url: string) {
      URL.revokeObjectURL(url);
    },
    sendFile: function () {
      const xhr = new XMLHttpRequest();
      xhr.upload.addEventListener('progress', (e) => {
        this.progress = Math.round((e.loaded * 100) / e.total);
      }, false);

      xhr.open('POST', `${this.baseUrl}request-upload`, true);
      xhr.addEventListener('readystatechange', () => {
        if (xhr.readyState === 4 && xhr.status >= 200 && xhr.status <= 300) {
          const response = JSON.parse(xhr.responseText) as TokenReponse;
          this.$emit('setToken', response.token);
        } else {
          let detail;
          try {
            detail = (JSON.parse(xhr.responseText) as ErrorReponse).detail;
          } catch (e) {
            detail = xhr.statusText;
          }
          this.error = this.$t('request_error', {error: detail});
        }
      });

      const fd = new FormData();
      fd.append('file', this.file);
      // Initiate a multipart/form-data upload
      xhr.send(fd);
    },
  },
});
</script>
