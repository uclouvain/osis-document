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
        class="dropzone"
        :class="{hovering: isHovering}"
        @dragenter="isHovering = true"
    >
      <input
          ref="fileInput"
          type="file"
          multiple
          :accept="mimetypes ? mimetypes.join(',') : null"
          @dragleave="isHovering = false"
          @change="onFilePicked"
      >
      {{ $t('uploader.drag_n_drop_label') }}
      <button
          class="btn btn-primary"
          type="button"
          @click="$refs.fileInput.click()"
      >
        <span class="glyphicon glyphicon-plus" />
        {{ $t('uploader.add_file_label') }}
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
          :upload-url="uploadUrl"
          :max-size="maxSize"
          :mimetypes="mimetypes"
          @delete="$delete(fileList, index)"
          @set-token="$set(tokens, index, $event)"
      />
    </ul>
    <input
        v-for="(token, index) in filteredTokens"
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

export default {
  name: 'Uploader',
  components: { UploadEntry },
  props: {
    name: {
      type: String,
      required: true,
    },
    uploadUrl: {
      type: String,
      required: true,
    },
    uploadText: {
      type: String,
      default: 'Upload file',
    },
    maxSize: {
      type: Number,
      default: 0,
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
    return {
      isHovering: false,
      fileList: [],
      tokens: [],
    };
  },
  computed: {
    filteredTokens: function () {
      return this.tokens.filter(t => !!t);
    },
  },
  methods: {
    humanizedSize,
    onFilePicked (e) {
      const files = e.target.files;
      this.fileList.push(...files);
      this.tokens.push(...Array(files.length).fill(null));
      this.isHovering = false;
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
