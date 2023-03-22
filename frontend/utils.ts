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
import {i18n} from './i18n';

export function humanizedSize(size: number): string {
  let i = 0;
  while (size >= 1024) {
    size /= 1024;
    ++i;
  }
  const unit = i18n.global.t(`units[${i}]`);
  return `${size.toFixed(2)} ${unit}`;
}


export async function doRequest(url: string, params?: object): Promise<unknown> {
  const response = await fetch(url, {
    headers: {'Content-Type': 'application/json'},
    ...params,
  });
  if (response.status >= 200 && response.status < 300) {
    return response.json();
  } else {
    throw new Error(response.statusText);
  }
}
