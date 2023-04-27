/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */
const { mergeConfig } = require('vite');

module.exports = {
  stories: [
    '../**/*.stories.@(js|jsx|ts|tsx)',
  ],
  staticDirs: ['../assets/', '../../osis_document/'],
  addons: [
    '@storybook/addon-essentials',
  ],
  framework: '@storybook/vue3',
  core: {
    'builder': '@storybook/builder-vite',
  },
  features: {
    'storyStoreV7': true,
  },
  async viteFinal (config, { configType }) {
    if (configType === 'PRODUCTION') {
      return mergeConfig(config, {
        base: './',
        build: {
          rollupOptions: {
            output: {
              sanitizeFileName: (name) => {
                /** Same as original but replace '_' by '' for storybook deployment
                 * See https://github.com/rollup/rollup/blob/master/src/utils/sanitizeFileName.ts */
                const INVALID_CHAR_REGEX = /[\u0000-\u001F"#$&*+,:;<=>?[\]^`{|}\u007F]/g;
                const DRIVE_LETTER_REGEX = /^[a-z]:/i;
                const match = DRIVE_LETTER_REGEX.exec(name);
                const driveLetter = match ? match[0] : '';
                // A `:` is only allowed as part of a windows drive letter (ex: C:\foo)
                // Otherwise, avoid them because they can refer to NTFS alternate data streams.
                return driveLetter + name.slice(driveLetter.length).replace(INVALID_CHAR_REGEX, '');
              },
            },
          },
        },
      });
    }
    return config;
  },
};
