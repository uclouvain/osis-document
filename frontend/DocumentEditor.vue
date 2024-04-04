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
  <div class="editor-container">
    <div class="wrapper">
      <div
          ref="viewerContainer"
          class="viewerContainer"
          tabindex="0"
      >
        <div class="pdfViewer" ref="pdfViewer" />
      </div>
    </div>

    <!-- Actions-->
    <div
        class="btn-toolbar"
        role="toolbar"
    >
      <ToolbarPagination
          v-if="pages && pagination"
          :current-page="currentPage"
          :pages="pages"
          @on-change-current-page="changeCurrentPage"
      />
      <ToolbarRotation
          v-if="rotation"
          :current-rotation="rotations[currentPage - 1] || 0"
          @on-rotate="rotate"
      />
      <ToolbarZoom
          v-if="zoom && currentZoom"
          :current-zoom="currentZoom"
          @on-zoom-in="zoomIn"
          @on-zoom-out="zoomOut"
          @on-set-scale="setScale"
      />
      <ToolbarAnnotation
          v-if="highlight"
          icon="fa-highlighter"
          :is-activated="highlightingColor != ''"
          :color="highlightingColor"
          class-prefix="bg"
          :colors="{
            warning: '#ffff00',
            danger: '#ff0000',
            info: '#0000ff',
            success: '#00ff00',
          }"
          @on-change="setHighlight"
      />
      <ToolbarAnnotation
          v-if="comment"
          icon="fa-message"
          :is-activated="commentingColor != ''"
          :color="commentingColor"
          class-prefix="text"
          :colors="{
            danger: '#a94442',
            warning: '#ffff00',
            info: '#31708f',
            success: '#3c763d',
            muted: '#ffffff',
          }"
          @on-change="setCommenting"
      />

      <!-- Saving -->
      <button
          type="button"
          class="btn"
          :class="needsToBeSaved ? 'btn-primary' : 'btn-default disabled'"
          @click="save"
      >
        <span
            class="fas"
            :class="savingInProgress ? 'fa-spinner fa-spin-pulse' : `fa-save ${needsToBeSaved && 'fa-beat-fade'}`"
        />
      </button>
    </div>
    <p
        v-if="error"
        class="text-danger"
    >
      {{ error }}
    </p>
  </div>
</template>

<script lang="ts">
import {defineComponent, markRaw, toRaw} from 'vue';
import ToolbarAnnotation from "./components/ToolbarAnnotation.vue";
import ToolbarZoom from "./components/ToolbarZoom.vue";
import ToolbarRotation from "./components/ToolbarRotation.vue";
import ToolbarPagination from "./components/ToolbarPagination.vue";
import {doRequest} from "./utils";

import * as pdfjs from 'pdfjs-dist';
import {AnnotationEditorParamsType, AnnotationEditorType} from 'pdfjs-dist';
import {EventBus, PDFViewer} from "pdfjs-dist/web/pdf_viewer";
import "pdfjs-dist/web/pdf_viewer.css";
import type {PDFPageView} from "pdfjs-dist/types/web/pdf_page_view";
import type {FileUpload, TokenReponse} from "./interfaces";

pdfjs.GlobalWorkerOptions.workerSrc = '/static/pdfjs/pdf.worker.min.js';

/**
 * TODO: Existing annotations cannot be edited, so watch for https://github.com/mozilla/pdf.js/issues/15403
 * Overall PDF Editing is tracked in https://github.com/mozilla/pdf.js/projects/9?fullscreen=true
 */
export default defineComponent({
  name: 'DocumentEditor',
  components: {ToolbarPagination, ToolbarRotation, ToolbarZoom, ToolbarAnnotation},
  props: {
    value: {
      type: String,
      required: true,
    },
    baseUrl: {
      type: String,
      required: true,
    },
    pagination: {
      type: Boolean,
      default: true,
    },
    zoom: {
      type: Boolean,
      default: true,
    },
    comment: {
      type: Boolean,
      default: true,
    },
    highlight: {
      type: Boolean,
      default: true,
    },
    rotation: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      token: this.value,
      rotations: {} as Record<number, number>,
      highlightingColor: '',
      commentingColor: '',
      loading: true,
      error: '',
      currentPage: 1,
      currentZoom: '',
      hasAnnotations: false,
      savingInProgress: false,
      interval: null as number | null,
      pages: 1,
      pdfDocument: undefined as pdfjs.PDFDocumentProxy | undefined,
      viewer: undefined as PDFViewer | undefined,
    };
  },
  computed: {
    hasBeenRotated() {
      return this.rotations && Object.keys(this.rotations).length !== 0;
    },
    needsToBeSaved() {
      return this.hasBeenRotated || this.hasAnnotations;
    },
  },
  mounted() {
    this.pdfDocument = undefined;
    void this.getFile();

    // Bind external DOM events
    const eventNames = [
      'changeCurrentPage',
      'rotate',
      'zoomIn',
      'zoomOut',
      'setScale',
      'setHighlight',
      'setCommenting',
      'save',
    ] as const;
    for (const eventName of eventNames) {
      (this.$el as HTMLDivElement).addEventListener(eventName, ((evt: CustomEvent<undefined | number>) => {
        // never is a way for TS to specify that all cases are covered
        void this[eventName](evt.detail as never);
      }) as EventListener);
    }
  },
  unmounted() {
    this.stopWatchingAnnotations();
  },
  methods: {
    getFile: async function () {
      if (this.token === 'FileInfectedException') {
        this.error = this.$t('view_entry.file_infected');
      } else {
        try {
          // Fetch document and inject into viewer
          const file = await doRequest(`${this.baseUrl}metadata/${this.token}`) as FileUpload;
          const pdfDocument = await pdfjs.getDocument(file.url).promise;

          // @ts-ignore bad typing from lib, see https://github.com/mozilla/pdf.js/pull/16362
          const viewer = new PDFViewer({
            container: this.$refs.viewerContainer as HTMLDivElement,
            eventBus: new EventBus(),
            viewer: this.$refs.pdfViewer as HTMLDivElement,
          });
          viewer.setDocument(pdfDocument);

          // Init pagination
          viewer.eventBus.on("pagechanging", (e: { pageNumber: number; }) => {
            this.currentPage = e.pageNumber;
            const externalEvent = new CustomEvent('pageChange', {detail: {pageNumber: e.pageNumber}});
            (this.$el as HTMLDivElement).dispatchEvent(externalEvent);
          });
          viewer.eventBus.on("pagesinit", () => {
            this.currentZoom = viewer.currentScaleValue = "auto";
          });
          this.pages = pdfDocument.numPages;
          const externalEvent = new CustomEvent('numPages', {detail: {numPages: pdfDocument.numPages}});
          (this.$el as HTMLDivElement).dispatchEvent(externalEvent);

          // Mark the following variables as not reactive as it messes up with proxies
          this.pdfDocument = markRaw(pdfDocument);
          this.viewer = markRaw(viewer);

        } catch (e) {
          this.error = (e as Error).message;
        }
      }
      this.loading = false;
    },
    rotate(rotation: number) {
      // @ts-ignore bad typing from lib, see https://github.com/mozilla/pdf.js/pull/16362
      (this.viewer?.getPageView(this.currentPage - 1) as PDFPageView).update({rotation});
      this.viewer?.update();  // To correctly display annotation layers after a rotation
      if (rotation !== 0) {
        this.rotations[this.currentPage - 1] = rotation;
      } else {
        delete this.rotations[this.currentPage - 1];
      }
    },
    changeCurrentPage(pageNum: number) {
      (this.viewer as PDFViewer).currentPageNumber = pageNum;
    },
    zoomIn() {
      const viewer = this.viewer as PDFViewer;
      viewer.increaseScale({scaleFactor: 1.1});
      this.currentZoom = viewer.currentScale.toString();
    },
    zoomOut() {
      const viewer = this.viewer as PDFViewer;
      viewer.decreaseScale({scaleFactor: 1.1});
      this.currentZoom = viewer.currentScale.toString();
    },
    setScale(scale: string) {
      (this.viewer as PDFViewer).currentScaleValue = scale;
      this.currentZoom = scale;
    },
    startWatchingAnnotations: function () {
      if (!this.interval) {
        this.interval = window.setInterval(() => this.updateNeedsToBeSaved(), 500);
      }
    },
    stopWatchingAnnotations: function () {
      this.interval && window.clearInterval(this.interval);
      this.interval = null;
    },
    setHighlight(color: string) {
      const viewer = this.viewer as PDFViewer;
      this.commentingColor = '';
      this.highlightingColor = color;
      if (color) {
        this.startWatchingAnnotations();
        viewer.annotationEditorMode = AnnotationEditorType.INK;
        viewer.annotationEditorParams = {
          type: AnnotationEditorParamsType.INK_THICKNESS,
          value: 10,
        };
        viewer.annotationEditorParams = {
          type: AnnotationEditorParamsType.INK_OPACITY,
          value: 50,
        };
        viewer.annotationEditorParams = {
          type: AnnotationEditorParamsType.INK_COLOR,
          value: color,
        };
      } else {
        this.stopWatchingAnnotations();
        viewer.annotationEditorMode = AnnotationEditorType.NONE;
      }
    },
    setCommenting(color: string) {
      const viewer = this.viewer as PDFViewer;
      this.highlightingColor = '';
      this.commentingColor = color;
      if (color) {
        this.startWatchingAnnotations();
        viewer.annotationEditorMode = AnnotationEditorType.FREETEXT;
        viewer.annotationEditorParams = {
          type: AnnotationEditorParamsType.FREETEXT_SIZE,
          value: 10,
        };
        viewer.annotationEditorParams = {
          type: AnnotationEditorParamsType.FREETEXT_COLOR,
          value: color,
        };
      } else {
        this.stopWatchingAnnotations();
        viewer.annotationEditorMode = AnnotationEditorType.NONE;
      }
    },
    updateNeedsToBeSaved() {
      this.hasAnnotations = !!this.pdfDocument && this.pdfDocument.annotationStorage.size > 0;
    },
    async save() {
      if (!this.needsToBeSaved) {
        return false;
      }
      this.savingInProgress = true;
      this.setCommenting('');
      const data = await (this.pdfDocument as pdfjs.PDFDocumentProxy).saveDocument();
      const blob = new Blob([data], {type: "application/pdf"});
      // Initiate a multipart/form-data upload
      const fd = new FormData();
      fd.append('file', blob);
      fd.append('rotations', JSON.stringify(toRaw(this.rotations)));
      try {
        const response = await doRequest(`${this.baseUrl}save-editor/${this.token}`, {
          method: 'POST',
          headers: undefined,  // the browser will handle it
          body: fd,
        }) as TokenReponse;
        this.rotations = {};
        this.hasAnnotations = false;
        this.token = response.token;
        void this.getFile();
      } catch (e) {
        this.error = (e as Error).message;
      }
      this.savingInProgress = false;
    },
  },
});
</script>

<style lang="scss">
.editor-container {
  height: 95vh;
  width: auto;
  display: flex;
  flex-direction: column;
}

.wrapper {
  position: relative;
  flex-grow: 1;
}

.viewerContainer {
  overflow: auto;
  position: absolute;
  width: 100%;
  height: 100%;
  background: #666;
}

:root {
  --page-margin: 1px auto -8px;
  --page-border: 9px solid transparent;
  --spreadHorizontalWrapped-margin-LR: -3.5px;
  --loading-icon-delay: 400ms;
}

@media screen and (forced-colors: active) {
  :root {
    --page-margin: 8px auto -1px;
    --page-border: 1px solid CanvasText;
    --spreadHorizontalWrapped-margin-LR: 3.5px;
  }
}

.pdfViewer .canvasWrapper {
  overflow: hidden;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.pdfViewer .page {
  direction: ltr;
  width: 816px;
  height: 1056px;
  margin: var(--page-margin);
  position: relative;
  overflow: visible;
  border: var(--page-border);
  background-clip: content-box;
  background-color: rgba(255, 255, 255, 1);
}

.pdfViewer:is(.scrollHorizontal, .scrollWrapped) {
  margin-inline: 3.5px;
  text-align: center;
}

.pdfViewer.scrollHorizontal {
  white-space: nowrap;
}

.pdfViewer:is(.scrollHorizontal, .scrollWrapped) .page {
  margin-inline: var(--spreadHorizontalWrapped-margin-LR);
}

.pdfViewer .page canvas {
  margin: 0;
  display: block;
}

.pdfViewer .page canvas .structTree {
  contain: strict;
}

.pdfViewer .page canvas[hidden] {
  display: none;
}

.pdfViewer .page canvas[zooming] {
  width: 100%;
  height: 100%;
}

.pdfViewer .page.loadingIcon::after {
  position: absolute;
  top: 0;
  left: 0;
  content: "";
  width: 100%;
  height: 100%;
  background: url("/static/pdfjs/loading-icon.gif") center no-repeat;
  display: none;
  /* Using a delay with background-image doesn't work,
     consequently we use the display. */
  transition-property: display;
  transition-delay: var(--loading-icon-delay);
  z-index: 5;
  contain: strict;
}

.pdfViewer .page.loading::after {
  display: block;
}

.pdfViewer .page:not(.loading)::after {
  transition-property: none;
  display: none;
}
</style>
