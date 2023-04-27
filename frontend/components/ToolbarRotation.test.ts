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
import ToolbarRotation from "./ToolbarRotation.vue";

const props = {
  currentRotation: 0,
};

it('should mount', () => {
  const wrapper = mount(ToolbarRotation, {props});
  expect(wrapper.html()).toMatchSnapshot();
});

it('should emit events', async () => {
  const wrapper = mount(ToolbarRotation, {props});
  await wrapper.findAll('button')[0].trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onRotate.0.0', -90);
  await wrapper.findAll('button')[1].trigger('click');
  expect(wrapper.emitted()).toHaveProperty('onRotate.1.0', 90);
});
