var p=Object.defineProperty;var o=(e,t)=>p(e,"name",{value:t,configurable:!0});import{V as m}from"./ViewEntry-d0ae75cb.js";import{d as f,a as r,F as b,r as g,o as s,i as y,j as h}from"./vue.esm-bundler-f0fdd64c.js";import{_ as v,c as a}from"./ViewingModal-13dc53c4.js";import"./i18n-fc0516a7.js";const l=f({name:"DocumentVisualizer",components:{ViewEntry:m},props:{baseUrl:{type:String,required:!0},values:{type:Array,required:!0}}}),z={class:"media-list"};function V(e,t,F,_,I,S){const u=h("ViewEntry");return s(),r("ul",z,[(s(!0),r(b,null,g(e.values,(d,i)=>(s(),y(u,{id:i.toString(),key:i,value:d,"base-url":e.baseUrl,"is-editable":!1},null,8,["id","value","base-url"]))),128))])}o(V,"_sfc_render");const c=v(l,[["render",V]]);l.__docgenInfo={displayName:"DocumentVisualizer",exportName:"default",description:"",tags:{},props:[{name:"baseUrl",type:{name:"string"},required:!0},{name:"values",type:{name:"string[]"},required:!0}]};const n=o(({response:e,...t})=>(a.restore(),e&&a.get("*",e),{components:{DocumentVisualizer:c},setup(){return{args:t}},template:'<DocumentVisualizer base-url="/" :values="[]" v-bind="args" />'}),"VisualizerTemplate"),A=n.bind({}),L=n.bind({});L.args={values:["77d4b8f6-ee55-4c40-b118-e9fffd796198"],response:{mimetype:"application/vnd.oasis.opendocument.text",size:82381,url:"./placeholder.odt",name:"test document"}};const B=n.bind({});B.args={values:["77d4b8f6-ee55-4c40-b118-e9fffd796198"],response:{mimetype:"application/pdf",size:82381,url:"./placeholder.pdf",name:"test document"}};const T=n.bind({});T.args={values:["77d4b8f6-ee55-4c40-b118-e9fffd796198"],response:{mimetype:"image/jpeg",size:38329,url:"./placeholder.jpeg",name:"test image"}};const D=n.bind({});D.args={values:["77d4b8f6-ee55-4c40-b118-e9fffd796198"],response:new Promise(e=>setTimeout(()=>e(200),2e6))};const w=n.bind({});w.args={values:["77d4b8f6-ee55-4c40-b118-e9fffd796198"],response:404};const U={parameters:{storySource:{source:`/*
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

import DocumentVisualizer from './DocumentVisualizer.vue';
import type {MockResponse} from 'fetch-mock';
import fetchMock from 'fetch-mock';
import type {Meta, StoryFn} from "@storybook/vue3";

const VisualizerTemplate: StoryFn<typeof DocumentVisualizer & { response: MockResponse }> = ({response, ...args}) => {
  fetchMock.restore();
  if (response) {
    fetchMock.get('*', response);
  }
  return {
    components: {DocumentVisualizer},
    setup() {
      return {args};
    },
    template: '<DocumentVisualizer base-url="/" :values="[]" v-bind="args" />',
  };
};

export const Empty = VisualizerTemplate.bind({});

export const Basic = VisualizerTemplate.bind({});
Basic.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'application/vnd.oasis.opendocument.text',
    size: 82381,
    url: './placeholder.odt',
    name: 'test document',
  },
};

export const PDF = VisualizerTemplate.bind({});
PDF.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'application/pdf',
    size: 82381,
    url: './placeholder.pdf',
    name: 'test document',
  },
};

export const Image = VisualizerTemplate.bind({});
Image.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: {
    mimetype: 'image/jpeg',
    size: 38329,
    url: './placeholder.jpeg',
    name: 'test image',
  },
};

export const Loading = VisualizerTemplate.bind({});
Loading.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: new Promise(res => setTimeout(() => res(200), 2000000)),
};

export const NotFound = VisualizerTemplate.bind({});
NotFound.args = {
  values: ['77d4b8f6-ee55-4c40-b118-e9fffd796198'],
  response: 404,
};


export default {
  title: 'DocumentVisualizer',
  component: DocumentVisualizer,
} as Meta<typeof DocumentVisualizer>;
`,locationsMap:{empty:{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}},basic:{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}},pdf:{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}},image:{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}},loading:{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}},"not-found":{startLoc:{col:92,line:32},endLoc:{col:1,line:44},startBody:{col:92,line:32},endBody:{col:1,line:44}}}}},title:"DocumentVisualizer",component:c},M=["Empty","Basic","PDF","Image","Loading","NotFound"];export{L as Basic,A as Empty,T as Image,D as Loading,w as NotFound,B as PDF,M as __namedExportsOrder,U as default};
//# sourceMappingURL=DocumentVisualizer.stories-3962b3cc.js.map
