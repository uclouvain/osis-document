/// <reference types="vitest" />
import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue';
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite';
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    VueI18nPlugin({
      include: [path.resolve(__dirname, './frontend/locales/**')],
    }),
  ],
  mode: 'production',
  define: {
    'process.env.NODE_ENV': process.env.NODE_ENV === 'test' ? '"test"' : '"production"',
  },
  build: {
    emptyOutDir: false,
    lib: {
      // what to build
      name: 'OsisDocument',
      // This is to have multiple UMD builds, until something like https://github.com/vitejs/vite/pull/10609
      entry: process.env.VITE_BUILD_EDITOR ? 'frontend/editor.ts' : 'frontend/main.ts',
      formats: ['umd'],
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled into library
      external: ['vue', 'vue-i18n', '@vue/runtime-dom'],
      output: {
        // Provide global variables to use in the UMD build for externalized deps
        globals: {
          vue: 'Vue',
          'vue-i18n': 'VueI18n',
          '@vue/runtime-dom': 'Vue',
        },
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'editor') {
            return 'osis-document-editor.umd.min.js';
          }
          return "osis-document.umd.min.js";
        },
        assetFileNames: () => {
          if (process.env.VITE_BUILD_EDITOR) {
            return 'osis-document-editor.[ext]';
          }
          return "osis-document.[ext]";
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['frontend/test.setup.ts'],
    minThreads:0,
    maxThreads:1,
    coverage: {
      provider: 'istanbul',
      all: true,
      enabled: true,
      perFile: true,
      branches: 100,
      statements: 100,
      include: ['frontend'],
      exclude: [
        "frontend/locales/",
        "frontend/node_modules/",
        "frontend/.storybook",
        "frontend/**/*.stories.{ts,js}",
      ],
    },
  },
});
