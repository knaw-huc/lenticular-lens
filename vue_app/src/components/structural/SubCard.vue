<template>
  <div class="bg-white border p-3"
       v-bind:class="{'mt-4': !isFirst && !smallSpacing, 'mt-2': !isFirst && smallSpacing, 'is-invalid': hasError}">
    <div v-if="hasColumns || hasCollapse || label || hasInfo || addButton"
         class="row align-items-center justify-content-between">
      <div v-if="hasCollapse" class="col-auto">
        <fa-icon icon="chevron-down" size="lg" v-b-toggle="id"></fa-icon>
      </div>

      <div v-if="label" class="col-auto pr-0" v-bind:class="{'mr-auto': !hasInfo && !addButton}">
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
            addButton: String,
            hasError: {
                type: Boolean,
                default: false
            },
            hasCollapse: {
                type: Boolean,
                default: false
            },
            hasInfo: {
                type: Boolean,
                default: false
            },
            hasColumns: {
                type: Boolean,
                default: false
            },
            isFirst: {
                type: Boolean,
                default: false,
            },
            smallSpacing: {
                type: Boolean,
                default: false,
            },
        },
    };
</script>