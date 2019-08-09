<template>
  <div class="border px-4 pt-2 mt-4 bg-light"
       v-bind:class="[{'is-invalid': hasError}, showContent ? 'pb-4' : 'pb-2']">
    <div class="row flex-nowrap align-items-center justify-content-between sticky-top py-2 bg-light"
         v-bind:class="showContent ? 'border-bottom' : {}">
      <div class="col-auto">
        <octicon name="chevron-down" scale="3" v-b-toggle="id"></octicon>
      </div>

      <div class="col-auto" v-bind:class="{'flex-fill': fillLabel}" v-b-toggle="id">
        <edit-label v-if="!label" :value="value" :required="true" @input="$emit('input', $event)"/>
        <div v-else class="h2">{{ label }}</div>

        <slot name="title-extra"></slot>
      </div>

      <slot name="columns"></slot>
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