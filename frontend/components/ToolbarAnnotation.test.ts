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

import {it, expect} from 'vitest';
import {mount} from "@vue/test-utils";
import ToolbarAnnotation from "./ToolbarAnnotation.vue";

const props = {
  isActivated: false,
  color: '',
  classPrefix: 'bg',
  icon: 'hightlighy',
  colors: {'danger': '#ff0000', 'warning': '#ffff00'},
};

it('should mount', () => {
  const wrapper = mount(ToolbarAnnotation, {props});
  expect(wrapper.html()).toMatchSnapshot();
});

it('should emit default color when not activated', async () => {
  const wrapper = mount(ToolbarAnnotation, {props});
  await wrapper.find('.btn-default:not(.dropdown-toggle)').trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onChange.0.0', '#ff0000');
});

it('should emit no color when activated', async () => {
  const wrapper = mount(ToolbarAnnotation, {
    props: {
      ...props,
      isActivated: true,
    },
  });
  await wrapper.find('.btn-primary').trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onChange.0.0', '');
});

it('should emit chosen color', async () => {
  const wrapper = mount(ToolbarAnnotation, {props});
  await wrapper.find('a.bg-warning').trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onChange.0.0', '#ffff00');
});
