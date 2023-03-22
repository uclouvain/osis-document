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

import {createI18n} from 'vue-i18n';

const messages = {
  en: {
    uploader: {
      specific_nb_drag_n_drop_label: 'Drag and drop one file here | Drag and drop {count} files here',
      min_max_drag_n_drop_label: 'Drag and drop between {min} and {max} files here',
      min_drag_n_drop_label: 'Drag and drop at least one file here | Drag and drop at least {count} files here',
      max_drag_n_drop_label: 'Drag and drop your file here | Drag and drop your files here (maximum {count})',
      drag_n_drop_label: 'Drag and drop your files here',
      add_file_label: 'or click here',
      max_size_label: '(max size {size})',
      trigger_upload: 'Upload',
    },
    upload_entry: {
      completion: '{progress}% uploaded',
      too_large: 'File is too large',
      wrong_type: 'The file must have the following type: "{types}" | The file must have one of the following types: "{types}"',
    },
    view_entry: {
      rotate_left: 'Rotate image left',
      rotate_right: 'Rotate image right',
      loading: "Loading...",
      close: "Close",
      save: "Save",
      file_infected: "The referenced file appears to be infected with a virus",
    },
    error: 'Error: {error}',
    request_error: 'Request error: {error}',
    units: ['B', 'KB', 'MB', 'GB', 'TB'],
  },
  'fr-be': {
    uploader: {
      specific_nb_drag_n_drop_label: 'Glissez-déposez ici un fichier | Glissez-déposez ici {count} fichiers',
      min_max_drag_n_drop_label: 'Glissez-déposez ici entre {min} et {max} fichiers',
      min_drag_n_drop_label: 'Glissez-déposez ici au-moins un fichier | Glissez-déposez ici au-moins {count} fichiers',
      max_drag_n_drop_label: 'Glissez-déposez ici votre fichier | Glissez-déposez ici vos fichiers (maximum {count})',
      drag_n_drop_label: 'Glissez-déposez ici vos fichiers',
      add_file_label: 'ou cliquez-ici',
      max_size_label: '(taille maximum {size})',
      trigger_upload: 'Transférer',
    },
    upload_entry: {
      completion: '{progress}% transférés',
      too_large: 'Le fichier est trop lourd',
      wrong_type: 'Le fichier doit être du type "{types}" | Le fichier doit être d\'un des types suivants : "{types}"',
    },
    view_entry: {
      rotate_left: "Faire pivoter l'image à gauche",
      rotate_right: "Faire pivoter l'image à droite",
      loading: "Chargement...",
      close: "Fermer",
      save: "Enregistrer",
      file_infected: "Le fichier référencé semble infecté par un virus",
    },
    error: 'Erreur : {error}',
    request_error: 'Erreur lors de la requête : {error}',
    units: ['o', 'Ko', 'Mo', 'Go', 'To'],
  },
};

export const i18n = createI18n({
  locale: document.documentElement.lang || 'en',
  messages,
});