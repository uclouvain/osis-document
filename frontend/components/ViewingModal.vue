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
              @load="imageLoaded($event.target)"
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
                  class="btn btn-primary"
                  :disabled="!(rotation % 360)"
                  @click="saveRotation"
              >
                <i
                    class="fas"
                    :class="saved ? 'fa-check' : 'fa-save'"
                />
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

<script>
export default {
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
      type: Object,
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
  data: function () {
    return {
      // Image rotation set by user
      rotation: 0,
      // Original image dimensions (filled once loaded)
      originalHeight: null,
      originalWidth: null,
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
      if (this.rotation % 180) {
        transform += ` translate(${[-90, 270].includes(this.rotation % 360) ? '-50%' : '50%'}, -50%)`;
      } else if (this.rotation % 360) {
        transform += ` translate(0, -100%)`;
      }
      // When image is portrait, constraint the rotated image height (which is width) to modal width
      const height = (this.rotation % 180 && this.$refs.modal.clientWidth < this.originalHeight) ? (this.$refs.modal.clientWidth - 30) + 'px' : 'auto';
      return { transform, height };
    },
  },
  watch: {
    rotation: 'changeModalHeight',
  },
  mounted () {
    // The modal may be loaded hidden, thus the image has no dimensions, use bootstrap event
    jQuery(this.$el).on('shown.bs.modal', () => {
      if (!this.originalHeight) {
        this.imageLoaded(this.$refs.img);
      }
      this.changeModalHeight();
    });
    if (this.openOnMount) {
      jQuery(this.$el).modal('show');
    }
  },
  beforeDestroy () {
    jQuery(this.$el).modal('hide');
  },
  methods: {
    imageLoaded: function (img) {
      if (this.isImage) {
        // The image is loaded, better wait for for next rendering tick
        this.$nextTick(() => {
          this.originalHeight = img.clientHeight;
          this.originalWidth = img.clientWidth;
          this.changeModalHeight();
        });
      }
    },
    changeModalHeight: function () {
      if (!this.originalWidth) return 'auto';  // Image is not yet loaded
      if (this.rotation % 180 && this.$refs.modal.clientWidth < this.originalHeight) {
        // Handle case when image is too tall for width (portrait)
        this.modalHeight = this.$refs.modal.clientWidth * this.originalWidth / this.originalHeight + 30 + 'px';
      } else {
        this.modalHeight = (this.rotation % 180 ? this.originalWidth : this.originalHeight) + 30 + 'px';
      }
    },
    saveRotation: async function () {
      try {
        const response = await fetch(`${this.baseUrl}rotate-image/${this.value}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rotate: this.rotation }),
        });
        if (response.status === 200) {
          this.saved = true;
          this.rotation = 0;
          const data = await response.json();
          this.$emit('update-token', data.token);
          this.error = '';
        } else {
          this.error = response.statusText;
        }
      } catch (e) {
        this.error = e;
      }
    },
  },
};
</script>
