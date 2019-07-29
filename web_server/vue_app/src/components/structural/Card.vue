<template>
  <div class="border p-4 mt-4 bg-light" v-bind:class="{'is-invalid': hasError}">
    <div class="row flex-nowrap align-items-center justify-content-between">
      <div class="col-auto">
        <octicon name="chevron-down" scale="3" v-b-toggle="id"></octicon>
      </div>

      <div class="col-auto" v-bind:class="{'flex-fill': fillLabel}" v-b-toggle="id">
        <edit-label v-if="editableLabel" v-model="label" :required="true"/>
        <div v-else class="h2">{{ label }}</div>

        <slot name="title-extra"></slot>
      </div>

      <slot name="columns"></slot>
    </div>

    <slot name="header"></slot>

    <b-collapse :id="id" :ref="id" :accordion="type + '-accordion'" @show="$emit('show')" @hide="$emit('hide')">
      <slot></slot>
    </b-collapse>
  </div>
</template>

<script>
    export default {
        name: 'Card',
        props: {
            id: String,
            type: String,
            label: String,
            hasError: {
                type: Boolean,
                default: false,
            },
            editableLabel: {
                type: Boolean,
                default: false,
            },
            fillLabel: {
                type: Boolean,
                default: true,
            },
        },
    };
</script>