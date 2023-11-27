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

export default {
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
    crop_header: 'Please choose the part you want to keep.',
    crop: 'Crop',
    cancel: 'Cancel',
  },
  view_entry: {
    rotate_left: 'Rotate image left',
    rotate_right: 'Rotate image right',
    loading: "Loading...",
    close: "Close",
    save: "Save",
    file_infected: "The referenced file appears to be infected with a virus",
  },
  editor: {
    pagination: '{currentPage} of {pages}',
    zoom: {
      auto: "Automatic Zoom",
      'page-width': "Page Width",
      'page-fit': "Page Fit",
      'page-actual': "Actual Size",
    },
    colors: {
      warning: 'Yellow',
      danger: 'Red',
      info: 'Blue',
      success: 'Green',
      muted: 'White',
    },
  },
  error: 'Error: {error}',
  request_error: 'Request error: {error}',
  units: ['B', 'KB', 'MB', 'GB', 'TB'],
};
