var s=Object.defineProperty;var n=(e,r)=>s(e,"name",{value:r,configurable:!0});import{V as o,c as t}from"./ViewingModal-3749d52d.js";import"./vue.esm-bundler-f0fdd64c.js";import"./i18n-bd53e731.js";const a=n(e=>(t.restore().post("/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63",200).post("/rotate-image/12e68184-5cba-4b27-9988-609a6cc3be63",200),{components:{ViewingModal:o},setup(){return{args:e}},template:'<ViewingModal v-bind="args" base-url="/" />',unmounted(){t.restore()}}),"ModalImageTemplate"),i=a.bind({});i.args={name:"media",id:"1",file:{mimetype:"image/jpeg",size:82381,url:"placeholder.jpeg",name:"test image"},value:"12e68184-5cba-4b27-9988-609a6cc3be63",openOnMount:!0};const c=a.bind({});c.args={...i.args,file:{mimetype:"image/jpeg",size:82381,url:"portrait.jpeg",name:"test image"}};const u={parameters:{storySource:{source:`/*
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

import fetchMock from 'fetch-mock';
import ViewingModal from './ViewingModal.vue';
import type {Meta, StoryFn} from "@storybook/vue3";

const ModalImageTemplate: StoryFn<typeof ViewingModal> = (args) => {
  fetchMock.restore()
      .post('/change-metadata/12e68184-5cba-4b27-9988-609a6cc3be63', 200)
      .post('/rotate-image/12e68184-5cba-4b27-9988-609a6cc3be63', 200);

  return ({
    components: {ViewingModal},
    setup() {
      return {args};
    },
    template: '<ViewingModal v-bind="args" base-url="/" />',
    unmounted() {
      fetchMock.restore();
    },
  });
};

export const Landscape = ModalImageTemplate.bind({});
Landscape.args = {
  name: 'media',
  id: '1',
  file: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: 'placeholder.jpeg',
    name: 'test image',
  },
  value: '12e68184-5cba-4b27-9988-609a6cc3be63',
  openOnMount: true,
};

export const Portrait = ModalImageTemplate.bind({});
Portrait.args = {
  ...Landscape.args,
  file: {
    mimetype: 'image/jpeg',
    size: 82381,
    url: 'portrait.jpeg',
    name: 'test image',
  },
};

export default {
  title: 'ViewingModal',
  component: ViewingModal,
} as Meta<typeof ViewingModal>;
`,locationsMap:{landscape:{startLoc:{col:57,line:31},endLoc:{col:1,line:46},startBody:{col:57,line:31},endBody:{col:1,line:46}},portrait:{startLoc:{col:57,line:31},endLoc:{col:1,line:46},startBody:{col:57,line:31},endBody:{col:1,line:46}}}}},title:"ViewingModal",component:o},g=["Landscape","Portrait"];export{i as Landscape,c as Portrait,g as __namedExportsOrder,u as default};
//# sourceMappingURL=ViewingModal.stories-0e53b706.js.map
