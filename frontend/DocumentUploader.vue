<!--
  -
  -   OSIS stands for Open Student Information System. It's an application
  -   designed to manage the core business of higher education institutions,
  -   such as universities, faculties, institutes and professional schools.
  -   The core business involves the administration of students, teachers,
  -   courses, programs and so on.
  -
  -   Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
  <div
      ref="uploader"
      class="osis-document-uploader"
  >
    <div
        v-if="maxFiles === 0 || nbUploadedFiles < maxFiles"
        class="dropzone form-group"
        :class="{hovering: isDragging}"
        @dragenter="isDragging = true"
    >
      <input
          ref="fileInput"
          type="file"
          multiple
          :accept="mimetypes.length ? mimetypes.join(',') : undefined"
          @dragleave="isDragging = false"
          @change="onFilePicked"
      >
      {{ uploadText || dragNDropLabel }}
      <button
          class="btn btn-default"
          type="button"
          @click="($refs.fileInput as HTMLInputElement).click()"
      >
        <span class="glyphicon glyphicon-plus" />
        {{ uploadButtonText || $t('uploader.add_file_label') }}
      </button>
      <span v-if="maxSize">
        {{ $t('uploader.max_size_label', { size: humanizedSize(maxSize) }) }}
      </span>
    </div>

    <ul
        v-if="fileList"
        class="media-list"
    >
      <UploadEntry
          v-for="(file, index) in fileList"
          :key="index"
          :file="file"
          :base-url="baseUrl"
          :max-size="maxSize"
          :mimetypes="mimetypes"
          :automatic="automaticUpload"
          @delete="delete fileList[index]; delete tokens[index];"
          @set-token="tokens[index] = $event; delete fileList[index];"
      />
    </ul>
    <div
        v-if="!automaticUpload && Object.values(fileList).length"
        class="text-right form-group"
    >
      <button
          class="btn btn-default "
          type="button"
          @click="triggerUpload"
      >
        {{ $t('uploader.trigger_upload') }}
      </button>
    </div>

    <ul class="media-list">
      <ViewEntry
          v-for="(token, index) in filteredTokens"
          :id="`${name}-${index}`"
          :key="index"
          :value="token"
          :base-url="baseUrl"
          :editable="true"
          :editable-filename="editableFilename"
          @delete="delete tokens[index]"
          @update-token="tokens[index] = $event"
      />
    </ul>

    <input
        v-for="(token, index) in Object.values(cleanedTokens)"
        :key="`${name}_${index}`"
        type="hidden"
        :name="`${name}_${index}`"
        :value="token"
    >
  </div>
</template>

<script lang="ts">
import {humanizedSize} from './utils';
import UploadEntry from './components/UploadEntry.vue';
import ViewEntry from './components/ViewEntry.vue';
import EventBus from './event-bus';
import {defineComponent} from 'vue';

const EVENT_NAMESPACE = 'osisdocument:';
const ADD_EVENT = 'add';
const DELETE_EVENT = 'delete';

export default defineComponent({
  name: 'DocumentUploader',
  components: {UploadEntry, ViewEntry},
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
    minFiles: {
      type: Number,
      default: 0,
    },
    maxFiles: {
      type: Number,
      default: 0,
    },
  },
  data() {
    let indexGenerated = 0;
    return {
      isDragging: false,
      fileList: {} as Record<number, File>,
      tokens: Object.fromEntries(this.values.map(f => {
        indexGenerated++;
        return [indexGenerated, f];
      })) as Record<number, string | null>,
      indexGenerated,
    };
  },
  computed: {
    /** Token list without empty tokens */
    filteredTokens: function () {
      return Object.fromEntries(Object.entries(this.tokens).filter(e => !!e[1])) as Record<number, string>;
    },
    /** Token list without infected or invalid files */
    cleanedTokens: function () {
      return Object.fromEntries(Object.entries(this.tokens).filter(
          e => !!e[1] && !['FileInfectedException', 'UploadInvalidException'].includes(e[1]),
      ));
    },
    /** Number of file tokens ready to be submitted */
    nbUploadedFiles: function () {
      return Object.values(this.cleanedTokens).length;
    },
    /**
     * Customize the drag and drop button label depending on the limits
     * @returns {string} the drag and drop label
     */
    dragNDropLabel: function () {
      if (this.minFiles) {
        if (this.minFiles === this.maxFiles) {
          return this.$tc('uploader.specific_nb_drag_n_drop_label', this.minFiles);
        } else if (this.maxFiles) {
          return this.$t('uploader.min_max_drag_n_drop_label', {min: this.minFiles, max: this.maxFiles});
        } else {
          return this.$tc('uploader.min_drag_n_drop_label', this.minFiles);
        }
      } else if (this.maxFiles) {
        return this.$tc('uploader.max_drag_n_drop_label', this.maxFiles);
      }
      return this.$t('uploader.drag_n_drop_label');
    },
  },
  watch: {
    cleanedTokens: {
      handler(newTokens: Record<number, string>, oldTokens: Record<number, string>) {
        if (JSON.stringify(oldTokens) !== JSON.stringify(newTokens)) {
          const eventType = Object.keys(oldTokens).length > Object.keys(newTokens).length ? DELETE_EVENT : ADD_EVENT;
          const fileEvent = new CustomEvent(EVENT_NAMESPACE + eventType, {
            bubbles: true,
            detail: {newTokens, oldTokens},
          });
          (this.$refs.uploader as HTMLDivElement).dispatchEvent(fileEvent);
        }
      },
    },
  },
  mounted() {
    // Watch for external changes on hidden inputs
    jQuery('> input', (this.$el as HTMLDivElement)).on('change', (event) => {
      const $input = jQuery(event.target);
      if (!$input.val()) {
        // If an input is emptied, remove all
        this.tokens = {};
      }
    });
  },
  methods: {
    humanizedSize,
    triggerUpload() {
      EventBus.emit('upload');
    },
    onFilePicked(e: Event) {
      const files = (e.target as HTMLInputElement).files;
      files && Array.from(files).forEach(file => {
        this.indexGenerated++;
        this.fileList[this.indexGenerated] = file;
        this.tokens[this.indexGenerated] = null;
      });
      this.isDragging = false;
    },
  },
});
</script>

<style lang="scss">
.dropzone {
  border: dashed 2px #8cb0cc;
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
