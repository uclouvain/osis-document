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
            class="progress-bar"
            :class="progress !== 100 ? 'progress-bar-striped active': 'progress-bar-success'"
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
        <span class="glyphicon glyphicon-trash" />
      </button>
    </div>
  </li>
</template>

<script>
/**
 * This component goal is to upload a local file and emit a token
 */
import { humanizedSize } from '../utils';
import EventBus from '../event-bus';

export default {
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
  data () {
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
  mounted () {
    if (this.maxSize && this.file.size > this.maxSize) {
      this.error = this.$t('upload_entry.too_large');
    } else if (this.mimetypes.length && !this.mimetypes.includes(this.file.type)) {
      this.error = this.$tc('upload_entry.wrong_type', this.mimetypes.length, {types: this.mimetypes.join(', ')});
    } else if (this.automatic) {
      this.sendFile();
    } else {
      EventBus.$on('upload', this.sendFile);
    }
  },
  methods: {
    revokeUrl: function (url) {
      URL.revokeObjectURL(url);
    },
    sendFile: function () {
      const xhr = new XMLHttpRequest();
      const self = this;
      xhr.upload.addEventListener('progress', (e) => {
        /* istanbul ignore else */
        if (e.lengthComputable) {
          self.progress = Math.round((e.loaded * 100) / e.total);
        }
      }, false);

      xhr.upload.addEventListener('load', () => {
        self.progress = 100;
      }, false);
      xhr.open('POST', `${this.baseUrl}request-upload`, true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status >= 200 && xhr.status <= 300) {
          const response = JSON.parse(xhr.responseText);
          self.$emit('set-token', response.token);
        } else {
          let detail;
          try {
            detail = JSON.parse(xhr.responseText).detail;
          } catch (e) {
            detail = xhr.statusText;
          }
          self.error = self.$t('request_error', { error: detail });
        }
      };

      const fd = new FormData();
      fd.append('file', this.file);
      // Initiate a multipart/form-data upload
      xhr.send(fd);
    },
  },
};
</script>
