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
    <!-- progress bar -->
    <div
        v-if="loading"
        class="media-body"
    >
      <div class="progress">
        <div
            class="progress-bar progress-bar-striped active"
            role="progressbar"
            aria-valuenow="0"
            aria-valuemin="0"
            aria-valuemax="100"
            :style="{
              width: `100%`
            }"
        >
          <span class="sr-only">{{ $t('view_entry.loading') }}</span>
        </div>
      </div>
    </div>
    <div
        v-else-if="inPostProcessing"
        class="media-body"
    >
      <div
          class="progress"
          style="text-align: center"
      >
        <div
            class="progress-bar progress-bar-striped active"
            role="progressbar"
            aria-valuenow="0"
            aria-valuemin="0"
            aria-valuemax="100"
            :style="{
              width: postProcessingProgress.toString() + `%`
            }"
        >
          <span class="sr-only">{{ $t('view_entry.loading') }}</span>
        </div>
        <span class="align-items-center">Avancement du post processing : {{ postProcessingProgress }} %</span>
      </div>
    </div>
    <!-- error -->
    <template v-else-if="error">
      <div class="media-body">
        <span class="text-danger">{{ $t('error', { error }) }}</span>
      </div>
      <div class="media-right text-right">
        <button
            v-if="isEditable"
            class="btn btn-danger"
            type="button"
            @click="$emit('delete')"
        >
          <span class="fas fa-trash-alt" />
        </button>
      </div>
    </template>
    <!-- thumbnail -->
    <template v-else-if="file">
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
        <h4 class="media-heading">
          <div
              v-if="isEditable && editableFilename"
              class="input-group"
          >
            <input
                v-model="name"
                type="text"
                class="form-control"
                @input="saved = false"
            >
            <span
                v-if="extension"
                class="input-group-addon"
            >
              {{ extension }}
            </span>
            <span class="input-group-btn">
              <button
                  type="button"
                  :disabled="file.name === fullName"
                  class="btn btn-default"
                  @click="saveName"
              >
                <i :class="`fas fa-${saved ? 'check' : 'save'}`" />
              </button>
            </span>
          </div>
          <div v-else>
            {{ file.name }}
          </div>
          <small><span class="text-nowrap">{{ humanizedSize(file.size) }}</span> ({{ file.mimetype }})</small>
        </h4>
      </div>
      <!-- actions -->
      <div
          class="media-right text-right"
          :style="{'min-width': isViewableDocument ? '9.5em' : '7em'}"
      >
        <div class="btn-group">
          <a
              v-if="isViewableDocument"
              class="btn btn-default"
              data-toggle="modal"
              :data-target="`#modal-${formattedValue}`"
          >
            <span class="fas fa-eye" />
          </a>
          <a
              class="btn btn-default"
              target="_blank"
              :href="`${file.url}?dl=1`"
          >
            <span class="fas fa-download" />
          </a>
          <button
              v-if="isEditable"
              class="btn btn-danger"
              type="button"
              @click="$emit('delete')"
          >
            <span class="fas fa-trash-alt" />
          </button>
        </div>
      </div>
      <ViewingModal
          v-if="isViewableDocument"
          :id="formattedValue"
          :file="file"
          :is-editable="isEditable"
          :value="value"
          :base-url="baseUrl"
          @update-token="$emit('updateToken', $event)"
      />
    </template>
  </li>
</template>

<script lang="ts">
/**
 * This component's goal is to view an uploaded file and edit it
 */
import {doRequest, humanizedSize} from '../utils';
import ViewingModal from './ViewingModal.vue';
import {defineComponent} from 'vue';
import type {FileUpload, GetRemoteTokenResponse, PostProcessingProgressResult} from "../interfaces";

export default defineComponent({
  name: 'ViewEntry',
  components: {ViewingModal},
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
    isEditable: {
      type: Boolean,
      default: true,
    },
    editableFilename: {
      type: Boolean,
      default: true,
    },
    getProgressUrl: {
      type: String,
      default: "",
    },
    postProcessStatus: {
      type: String,
      default: "",
    },
    baseUuid: {
      type: String,
      default: "",
    },
    wantedPostProcess: {
      type: String,
      default: "",
    },
  },
  emits: {
    updateToken(token: string) {
      return token.length > 0;
    },
    delete() {
      return true;
    },
  },
  data() {
    return {
      file: null as FileUpload | null,
      loading: true,
      inPostProcessing: false,
      postProcessingProgress: 0,
      error: '',
      name: '',
      extension: '',
      saved: false,
      intervalProgress: setInterval(
          /* istanbul ignore next */
          () => undefined,
          300000),
      getRemoteTokenResponse: {token: ''} as GetRemoteTokenResponse,
    };
  },
  computed: {
    isImage: function () {
      return this.file?.mimetype.split('/')[0] === 'image';
    },
    isViewableDocument: function () {
      const mimetype = (this.file as FileUpload).mimetype;
      return mimetype.split('/')[0] === 'image' || mimetype === 'application/pdf';
    },
    formattedValue: function () {
      return this.value.replace(/:/g, '-');
    },
    fullName: {
      // The full name is composed of the file name and extension (if specified)
      get() {
        return `${this.name}${this.extension}`;
      },
      set: function (newValue: string) {
        const splitName = /^(.+)(\.[^.]+)$/.exec(newValue);
        if (splitName?.length === 3) {
          this.name = splitName[1];
          this.extension = splitName[2];
        } else {
          this.name = newValue;
          this.extension = '';
        }
      },
    },
  },
  watch: {
    value: 'getFile',
  },
  mounted() {
    void this.getFile();
  },
  /* istanbul ignore next */
  updated() {
    if (this.inPostProcessing){
      if ((this.getProgressUrl !== "" || this.getProgressUrl !== undefined) && this.postProcessingProgress !== 100){
        clearInterval(this.intervalProgress);
        this.intervalProgress = setInterval(/* istanbul ignore next */()=>{
          void this.getProgressPostProcessing();
        }, 3000);
      }
      if (this.postProcessingProgress === 100 ) {
        clearInterval(this.intervalProgress);
        this.inPostProcessing = false;
        void this.getFile();
      }
    }
  },
  unmounted() {
    clearInterval(this.intervalProgress);
  },
  methods: {
    humanizedSize,
    getFile: async function () {
      if (this.value === 'FileInfectedException') {
        this.error = this.$t('view_entry.file_infected');
      }
      else if (this.value === '' && this.postProcessingProgress !== 100){
        this.inPostProcessing = true;
        await this.getProgressPostProcessing();
      }
      else {
        if (this.value === ''){
          let body = JSON.stringify({
                uuid: this.baseUuid,
              });
          if (this.wantedPostProcess === '' || this.wantedPostProcess === undefined) {
            body = JSON.stringify({
                uuid: this.baseUuid,
                wanted_post_process: this.wantedPostProcess,
              });
          }
          this.getRemoteTokenResponse = await doRequest(`${this.baseUrl}read-token/${this.baseUuid}`,{
            method: 'POST',
            body: body,
          }) as GetRemoteTokenResponse;
        }
        const url = (this.getRemoteTokenResponse.token !== '') ? `${this.baseUrl}metadata/${this.getRemoteTokenResponse.token}` : `${this.baseUrl}metadata/${this.value}`;
        try {
          this.file = await doRequest(url) as FileUpload;
          this.fullName = this.file.name;
        } catch (e) {
          this.error = (e as Error).message;
        }
      }
      this.loading = false;
    },
    getProgressPostProcessing :async function(){
      /* istanbul ignore if -- @preserve */
      if (this.postProcessingProgress !== 100 && this.getProgressUrl !== "") {
        try {
          let url = '';
          if (this.wantedPostProcess){
            url = this.getProgressUrl + '?' + 'wanted_post_process=' + this.wantedPostProcess;
          }
          else {
            url = this.getProgressUrl;
          }
          const result = await doRequest(`${url}`, {
            method: 'GET',
          }) as PostProcessingProgressResult;
          this.postProcessingProgress = result.progress;
        } catch (e) {
          this.error = (e as Error).message;
        }
      }
    },
    saveName: async function () {
      try {
        await doRequest(`${this.baseUrl}change-metadata/${this.value}`, {
          method: 'POST',
          body: JSON.stringify({name: this.fullName}),
        });
        this.saved = true;
        (this.file as FileUpload).name = this.fullName;
      } catch (e) {
        this.error = (e as Error).message;
      }
    },
  },
});
</script>
