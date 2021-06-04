<template>
  <ul class="media-list">
    <ViewEntry
        v-for="(value, index) in values"
        :id="index.toString()"
        :key="index"
        :value="value"
        :base-url="baseUrl"
    />
  </ul>
</template>

<script>
import ViewEntry from './components/ViewEntry';

export default {
  name: 'Visualizer',
  components: { ViewEntry },
  props: {
    baseUrl: {
      type: String,
      required: true,
    },
    values: {
      type: Array,
      default: () => [],
    },
  },
};
</script>
