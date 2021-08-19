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
  <div>
    <div
        v-if="Object.values(filteredTokens).length < Math.max(limit, 1)"
        class="dropzone"
        :class="{hovering: isDragging}"
        @dragenter="isDragging = true"
    >
      <input
          ref="fileInput"
          type="file"
          multiple
          :accept="mimetypes ? mimetypes.join(',') : null"
          @dragleave="isDragging = false"
          @change="onFilePicked"
      >
      {{ uploadText || $tc('uploader.drag_n_drop_label', limit) }}
      <button
          class="btn btn-default"
          type="button"
          @click="$refs.fileInput.click()"
      >
        <span class="glyphicon glyphicon-plus" />
        {{ uploadButtonText || $t('uploader.add_file_label') }}
      </button>
      <span v-if="maxSize">
        {{ $t('uploader.max_size_label', { size: humanizedSize(maxSize) }) }}
      </span>
    </div>

    <ul class="media-list">
      <UploadEntry
          v-for="(file, index) in fileList"
          :key="index"
          :file="file"
          :base-url="baseUrl"
          :max-size="maxSize"
          :mimetypes="mimetypes"
          :automatic="automaticUpload"
          @delete="$delete(fileList, index); $delete(tokens, index);"
          @set-token="$set(tokens, index, $event); $delete(fileList, index);"
      />
    </ul>
    <button
        v-if="!automaticUpload && Object.values(fileList).length"
        class="btn btn-default pull-right"
        type="button"
        @click="triggerUpload"
    >
      {{ $t('uploader.trigger_upload') }}
    </button>

    <ul class="media-list">
      <ViewEntry
          v-for="(token, index) in filteredTokens"
          :id="index"
          :key="index"
          :value="token"
          :base-url="baseUrl"
          :editable="true"
          :editable-filename="editableFilename"
          @delete="$delete(tokens, index);"
          @update-token="$set(tokens, index, $event);"
      />
    </ul>

    <input
        v-for="(token, index) in Object.values(filteredTokens)"
        :key="`${name}_${index}`"
        type="hidden"
        :name="`${name}_${index}`"
        :value="token"
    >
  </div>
</template>

<script>
import { humanizedSize } from './utils';
import UploadEntry from './components/UploadEntry';
import ViewEntry from './components/ViewEntry';
import EventBus from './event-bus';

export default {
  name: 'Uploader',
  components: { UploadEntry, ViewEntry },
  props: {
    name: {
      type: String,
      required: true,
    },
    baseUrl: {
      type: String,
      required: true,
    },
    uploadText: {
      type: String,
      default: null,
    },
    uploadButtonText: {
      type: String,
      default: null,
    },
    maxSize: {
      type: Number,
      default: 0,
    },
    limit: {
      type: Number,
      default: 0,
    },
    automaticUpload: {
      type: Boolean,
      default: true,
    },
    editableFilename: {
      type: Boolean,
      default: true,
    },
    values: {
      type: Array,
      default: () => [],
    },
    mimetypes: {
      type: Array,
      default: () => [],
    },
  },
  data () {
    let indexGenerated = 0;
    return {
      isDragging: false,
      fileList: {},
      tokens: Object.fromEntries(this.values.map(f => {
        indexGenerated++;
        return [indexGenerated, f];
      })),
      indexGenerated,
    };
  },
  computed: {
    filteredTokens: function () {
      return Object.fromEntries(Object.entries(this.tokens).filter(e => !!e[1]));
    },
  },
  methods: {
    humanizedSize,
    triggerUpload() {
      EventBus.$emit('upload');
    },
    onFilePicked (e) {
      const files = e.target.files;
      Array.from(files).forEach(file => {
        this.indexGenerated++;
        this.$set(this.fileList, this.indexGenerated, file);
        this.$set(this.tokens, this.indexGenerated, null);
      });
      this.isDragging = false;
    },
  },
};
</script>

<style lang="scss">
.dropzone {
  border: dashed 3px #2e6da4;
  border-radius: 5px * 2;
  overflow: hidden;
  transition: all 1s;
  position: relative;
  padding: 1em;
  text-align: center;

  &:after {
    padding: 1em 3em;
    display: inline-block;
    text-align: center;
  }

  &.filled {
    border: solid 3px #4cae4c;
  }

  input {
    display: none;
    position: absolute;
    z-index: 3;
    padding: 20px 0;
    opacity: 0;
    width: 100%;
    height: 100%;
    top: 0;
  }

  &.hovering {
    border: dotted 3px #4cae4c;

    input {
      display: block;
    }
  }
}
</style>
