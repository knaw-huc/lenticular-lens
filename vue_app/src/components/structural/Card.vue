<template>
  <div class="border p-4 mt-4 bg-light" v-bind:class="{'is-invalid': hasError}">
    <div class="sticky-top bg-light py-2" v-bind:class="showContent ? 'border-bottom' : {}">
      <div class="row flex-nowrap align-items-center justify-content-between">
        <div class="col-auto">
          <fa-icon icon="chevron-down" size="2x" v-b-toggle="id"></fa-icon>
        </div>

        <div class="col-auto flex-shrink-1" v-bind:class="{'flex-fill': fillLabel}">
          <edit-label v-if="!label" :value="value" :required="true" @input="$emit('input', $event)" v-b-toggle="id"/>
          <div v-else class="h2" v-b-toggle="id">{{ label }}</div>

          <slot name="title-extra"></slot>
        </div>

        <slot name="columns"></slot>
      </div>
    </div>

    <slot name="header"></slot>

    <b-collapse :id="id" :ref="id" :accordion="type + '-accordion'" v-model="showContent"
                @show="$emit('show')" @hide="$emit('hide')">
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
            value: String,
            hasError: {
                type: Boolean,
                default: false,
            },
            fillLabel: {
                type: Boolean,
                default: true,
            },
        },
        data() {
            return {
                showContent: false
            };
        },
    };
</script>