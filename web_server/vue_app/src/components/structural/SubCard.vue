<template>
  <div class="bg-white border p-3 mt-4">
    <div v-if="hasColumns || hasCollapse || label || hasInfo || addButton"
         class="row align-items-center justify-content-between">
      <div v-if="hasCollapse" class="col-auto">
        <octicon name="chevron-down" scale="2" v-b-toggle="id"></octicon>
      </div>

      <div v-if="label" class="col-auto pr-0">
        <h3>{{ label }}</h3>
      </div>

      <div v-if="hasInfo" class="col-auto pl-0" v-bind:class="{'mr-auto': !addButton}">
        <slot name="info"></slot>
      </div>

      <slot name="columns"></slot>

      <div v-if="addButton" class="col-auto ml-auto">
        <button-add @click="$emit('add')" :title="addButton"/>
      </div>
    </div>

    <b-collapse v-if="hasCollapse" :id="id" :ref="id" :accordion="type + '-accordion'"
                @show="$emit('show')" @hide="$emit('hide')">
      <slot></slot>
    </b-collapse>

    <slot v-else></slot>
  </div>
</template>

<script>
    export default {
        name: 'SubCard',
        props: {
            id: String,
            type: String,
            label: String,
            hasCollapse: {
                type: Boolean,
                default: false
            },
            hasInfo: {
                type: Boolean,
                default: false
            },
            addButton: String,
            hasColumns: {
                type: Boolean,
                default: false
            },
        },
    };
</script>