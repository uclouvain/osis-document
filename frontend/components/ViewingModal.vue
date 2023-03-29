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
  <div
      :id="`modal-${id}`"
      class="modal fade"
      tabindex="-1"
      role="dialog"
  >
    <div
        class="modal-dialog modal-lg"
        role="document"
    >
      <div class="modal-content">
        <div class="modal-header">
          <button
              type="button"
              class="close"
              data-dismiss="modal"
              :aria-label="$t('view_entry.close')"
          >
            <span aria-hidden="true">&times;</span>
          </button>
          <h4 class="modal-title">
            {{ file.name }}
          </h4>
        </div>
        <div
            ref="modal"
            class="modal-body"
            style="transition: 500ms; overflow: hidden; max-width: 100%"
            :style="{height: modalHeight}"
        >
          <img
              v-if="isImage"
              ref="img"
              :src="file.url"
              :alt="file.name"
              class="img-responsive"
              style="transition: 500ms; transform-origin: top center; margin: 0 auto;"
              :style="imageStyle"
              @load="imageLoaded($event.target as HTMLImageElement)"
          >
          <div
              v-else
              class="embed-responsive embed-responsive-16by9"
          >
            <object
                :data="file.url"
                type="application/pdf"
                class="embed-responsive-item"
            >
              <embed
                  :src="file.url"
                  type="application/pdf"
              >
            </object>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div
                v-if="isImage && isEditable"
                class="col-sm-10 text-left"
            >
              <button
                  type="button"
                  class="btn btn-default"
                  @click="rotation -= 90"
              >
                <i class="fas fa-undo" />
              </button>
              <button
                  type="button"
                  class="btn btn-default"
                  @click="rotation += 90"
              >
                <i class="fas fa-redo" />
              </button>
              <button
                  type="button"
                  class="btn btn-default"
                  :disabled="!isRotated"
                  @click="saveRotation"
              >
                <i :class="`fas fa-${saved ? 'check' : 'save'}`" />
                {{ $t('view_entry.save') }}
              </button>
              <span
                  v-if="error"
                  class="text-danger"
              >
                {{ $t('error', { error }) }}
              </span>
            </div>
            <div class="col-sm-2 pull-right">
              <button
                  type="button"
                  class="btn btn-default"
                  data-dismiss="modal"
              >
                {{ $t('view_entry.close') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, nextTick} from 'vue';
import type {PropType} from 'vue';
import type {FileUpload, TokenReponse} from '../interfaces';
import {doRequest} from "../utils";

export default defineComponent({
  name: 'ViewingModal',
  props: {
    baseUrl: {
      type: String,
      required: true,
    },
    value: {
      type: String,
      required: true,
    },
    id: {
      type: String,
      required: true,
    },
    file: {
      type: Object as PropType<FileUpload>,
      required: true,
    },
    isEditable: {
      type: Boolean,
      default: true,
    },
    openOnMount: {
      type: Boolean,
      default: false,
    },
  },
  emits: {
    updateToken(token: string) {
      return token.length > 0;
    },
  },
  data: function () {
    return {
      // Image rotation set by user
      rotation: 0,
      // Original image dimensions (filled once loaded)
      originalHeight: null as number | null,
      originalWidth: null as number | null,
      // Programmatically controlled dimensions for modal
      modalHeight: 'auto',
      modalWidth: 'auto',
      error: '',
      saved: false,
    };
  },
  computed: {
    isImage: function () {
      return this.file.mimetype.split('/')[0] === 'image';
    },
    imageStyle: function () {
      let transform = `rotate(${this.rotation}deg)`;
      if (this.isQuarterRotated) {
        transform += ` translate(${this.isRotated90CounterClockwise ? '-50%' : '50%'}, -50%)`;
      } else if (this.isRotated) {
        transform += ` translate(0, -100%)`;
      }
      // When image is portrait, constraint the rotated image height (which is width) to modal width
      const modal = this.$refs.modal as HTMLDivElement;
      const height = (this.originalHeight && this.isQuarterRotated && modal.clientWidth < this.originalHeight)
          ? `${modal.clientWidth - 30}px`
          : 'auto';
      return {transform, height};
    },
    isRotated: function () {
      return this.rotation % 360;
    },
    isQuarterRotated: function () {
      // Check if the image is rotated at 90 or -90 degrees
      return this.rotation % 180;
    },
    isRotated90CounterClockwise: function () {
      // Check if the image is rotated at -90 degrees
      return [-90, 270].includes(this.rotation % 360);
    },
  },
  watch: {
    rotation: 'changeModalHeight',
  },
  mounted() {
    // The modal may be loaded hidden, thus the image has no dimensions, use bootstrap event
    jQuery(this.$el).on('shown.bs.modal', () => {
      if (!this.originalHeight) {
        void this.imageLoaded(this.$refs.img as HTMLImageElement);
      }
      this.changeModalHeight();
    });
    if (this.openOnMount) {
      jQuery(this.$el).modal('show');
    }
  },
  beforeUnmount() {
    jQuery(this.$el).modal('hide');
  },
  methods: {
    imageLoaded: async function (img: HTMLImageElement) {
      // The image is loaded, better wait for next rendering tick
      await nextTick();
      this.originalHeight = img.clientHeight;
      this.originalWidth = img.clientWidth;
      this.changeModalHeight();
    },
    changeModalHeight: function () {
      if (!this.originalWidth || !this.originalHeight) return 'auto';  // Image is not yet loaded
      const modal = this.$refs.modal as HTMLDivElement;
      if (this.isQuarterRotated && modal.clientWidth < this.originalHeight) {
        // Handle case when image is too tall for width (portrait)
        this.modalHeight = `${modal.clientWidth * this.originalWidth / this.originalHeight + 30}px`;
      } else {
        this.modalHeight = `${(this.isQuarterRotated ? this.originalWidth : this.originalHeight) + 30}px`;
      }
    },
    saveRotation: async function () {
      try {
        const data = await doRequest(`${this.baseUrl}rotate-image/${this.value}`, {
          method: 'POST',
          body: JSON.stringify({rotate: this.rotation}),
        }) as TokenReponse;
        this.saved = true;
        this.rotation = 0;
        this.$emit('updateToken', data.token);
        this.error = '';
      } catch (e) {
        this.error = (e as Error).message;
      }
    },
  },
});
</script>
