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
              aria-label="Close"
          >
            <span aria-hidden="true">&times;</span>
          </button>
          <h4 class="modal-title">
            {{ file.name }}
          </h4>
        </div>
        <div class="modal-body">
          <img
              v-if="isImage"
              :src="file.url"
              :alt="file.name"
              class="img-responsive"
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
          <button
              type="button"
              class="btn btn-default"
              data-dismiss="modal"
          >
            Close
          </button>
          <button
              v-if="isImage && isEditable"
              type="button"
              class="btn btn-primary"
          >
            Save changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ViewingModal',
  props: {
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
  },
  computed: {
    isImage: function () {
      return this.file.mimetype.split('/')[0] === 'image';
    },
  },
  beforeDestroy () {
    jQuery(this.$el).modal('hide');
  },
};
</script>
