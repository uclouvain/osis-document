<template>
  <ul class="media-list">
    <ViewEntry
        v-for="(value, index) in values"
        :id="index.toString()"
        :key="index"
        :value="value"
        :base-url="baseUrl"
        :is-editable="false"
    />
  </ul>
</template>

<script lang="ts">
import ViewEntry from './components/ViewEntry.vue';
import {defineComponent} from 'vue';
import type {PropType} from 'vue';

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
  },
});
</script>
