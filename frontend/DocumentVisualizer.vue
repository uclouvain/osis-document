<template>
  <ul class="media-list">
    <ViewEntry
        v-for="(value, index) in values"
        :id="index.toString()"
        :key="index"
        :value="value"
        :base-url="baseUrl"
        :is-editable="false"
        :getProgressUrl="getProgressUrl"
        :postProcessStatus="postProcessStatus"
        :baseUuid="baseUuid"
        :wantedPostProcess="wantedPostProcess"
    />
  </ul>
</template>

<script lang="ts">
import ViewEntry from './components/ViewEntry.vue';
import type {PropType} from 'vue';
import {defineComponent} from 'vue';

export default defineComponent({
  name: 'DocumentVisualizer',
  components: {ViewEntry},
  props: {
    baseUrl: {
      type: String,
      required: true,
    },
    values: {
      type: Array as PropType<string[]>,
      required: true,
    },
    postProcessStatus:{
      type : String,
      required: true
    },
    getProgressUrl:{
      type : String,
      required: true
    },
    baseUuid:{
      type : String,
      required: true
    },
    wantedPostProcess:{
      type : String,
      required: true
    },
  },
});
</script>
