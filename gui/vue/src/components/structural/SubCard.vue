<template>
  <div class="sub-card" v-bind:class="classes">
    <div v-if="hasColumns || hasCollapse || label || hasInfo || addButton"
         class="row align-items-center justify-content-between">
      <div v-if="hasCollapse" class="col-auto">
        <fa-icon icon="chevron-down" size="lg" v-b-toggle="id"></fa-icon>
      </div>

      <div v-if="label" class="col-auto pr-0" v-b-toggle="hasCollapse ? id : {}"
           v-bind:class="{'mr-auto': !hasInfo && !addButton && !hasMarginAuto}">
        <h5 v-if="this.size === 'xs'">{{ label }}</h5>
        <h4 v-if="this.size === 'sm'">{{ label }}</h4>
        <h3 v-else>{{ label }}</h3>
      </div>

      <div v-if="hasInfo" class="col-auto pl-0" v-bind:class="{'mr-auto': !addButton && !hasMarginAuto}">
        <slot name="info"></slot>
      </div>

      <slot name="columns"></slot>

      <div v-if="addButton" class="col-auto ml-auto">
        <button-add @click="$emit('add')" :title="addButton"/>
      </div>
    </div>

    <div v-if="hasExtraRow" class="row flex-nowrap align-items-center justify-content-between mt-4">
      <slot name="row-columns"></slot>
    </div>

    <b-collapse v-if="hasCollapse" :id="id" :ref="id" :accordion="type + '-accordion'" :visible="openCard"
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
            openCard: {
                type: Boolean,
                default: false,
            },
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
            hasMarginAuto: {
                type: Boolean,
                default: false
            },
            hasColumns: {
                type: Boolean,
                default: false
            },
            hasExtraRow: {
                type: Boolean,
                default: false
            },
            size: {
                type: String,
                default: '',
            },
            isFirst: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            classes() {
                return {
                    'mt-4': this.size === '' && !this.isFirst,
                    'mt-3': (this.size === 'xs' || this.size === 'sm') && !this.isFirst,
                    'is-invalid': this.hasError,
                    'small-card': this.size !== ''
                };
            },
        },
    };
</script>