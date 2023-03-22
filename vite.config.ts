/// <reference types="vitest" />
import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  mode: 'production',
  define: {
    'process.env.NODE_ENV': process.env.NODE_ENV === 'test' ? '"test"' : '"production"',
  },
  build: {
    lib: {
      // what to build
      name: 'OsisDocument',
      entry: 'frontend/main.ts',
      formats: ['umd'],
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled into library
      external: ['vue', 'vue-i18n','@vue/runtime-dom'],
      output: {
        // Provide global variables to use in the UMD build for externalized deps
        globals: {
          vue: 'Vue',
          'vue-i18n': 'VueI18n',
          '@vue/runtime-dom': 'Vue',
        },
        assetFileNames: "osis-document.[ext]",
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['frontend/test.setup.ts'],
    coverage: {
      provider: 'istanbul',
      all: true,
      enabled: true,
      perFile: true,
      branches: 100,
      statements: 100,
      include: ['frontend'],
      exclude: [
        "frontend/node_modules/",
        "frontend/.storybook",
        "frontend/**/*.stories.{ts,js}",
      ],
    },
  },
});
