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
import ToolbarPagination from "./ToolbarPagination.vue";

const props = {
  currentPage: 1,
  pages: 12,
};

it('should mount', () => {
  const wrapper = mount(ToolbarPagination, {props});
  expect(wrapper.html()).toMatchSnapshot();
});

it('should not emit on disabled previous button', async () => {
  const wrapper = mount(ToolbarPagination, {props});
  await wrapper.find('button.disabled').trigger('click');
  expect(wrapper.emitted('onChangeCurrentPage')).toBeFalsy();
});

it('should not emit on disabled next button', async () => {
  const wrapper = mount(ToolbarPagination, {
    props: {
      ...props,
      currentPage: 12,
    },
  });
  await wrapper.find('button.disabled').trigger('click');
  expect(wrapper.emitted('onChangeCurrentPage')).toBeFalsy();
});

it('should emit on next button', async () => {
  const wrapper = mount(ToolbarPagination, {props});
  await wrapper.findAll('button')[1].trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onChangeCurrentPage.0.0', 2);
});

it('should emit on previous button', async () => {
  const wrapper = mount(ToolbarPagination, {
    props: {
      ...props,
      currentPage: 7,
    },
  });
  await wrapper.findAll('button')[0].trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onChangeCurrentPage.0.0', 6);
});
