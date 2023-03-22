/*
 *
 *   OSIS stands for Open Student Information System. It's an application
 *   designed to manage the core business of higher education institutions,
 *   such as universities, faculties, institutes and professional schools.
 *   The core business involves the administration of students, teachers,
 *   courses, programs and so on.
 *
 *   Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   A copy of this license - GNU General Public License - is available
 *   at the root of the source code of this program.  If not,
 *   see http://www.gnu.org/licenses/.
 *
 */

module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:storybook/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    '@vue/typescript/recommended',
    '@vue/eslint-config-typescript/recommended',
  ],
  overrides: [{
    files: ['.eslintrc.js'],
    extends: ['eslint:recommended'],
    env: {
      node: true,
    },
  }, {
    files: ['vite.config.ts', 'frontend/.storybook/main.ts'],
    extends: ['eslint:recommended'],
    parserOptions: {
      project: ['./tsconfig.vite.json'],
    },
    env: {
      node: true,
    },
  }],
  ignorePatterns: ['osis_history/static/**/*.js'],
  globals: {
    jQuery: 'readonly',
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    project: ['./tsconfig.json'],
    tsconfigRootDir: __dirname,
    ecmaVersion: 2021,
    sourceType: 'module',
  },
  plugins: ['vue', '@typescript-eslint'],
  rules: {
    'vue/html-indent': ['error', 2, {
      attribute: 2,
    }],
    'vue/no-v-html': 'off',
    'comma-dangle': ['error', 'always-multiline'],
    semi: ['error', 'always'],
    eqeqeq: ['error', 'always'],
    'prefer-const': ['error', {
      destructuring: 'any',
      ignoreReadBeforeAssign: false,
    }],
    "@typescript-eslint/ban-ts-comment": [
      "error",
      {
        "ts-ignore": "allow-with-description",
      },
    ],
  },
};
