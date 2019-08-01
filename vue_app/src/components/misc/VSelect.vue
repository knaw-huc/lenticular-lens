<template>
    <select class="border-0 btn-outline-info form-control h-auto shadow" v-on="inputListeners" v-bind="$attrs" :value="value"><slot/></select>
</template>

<script>
    export default {
        inheritAttrs: false,
        props: ['value'],
        computed: {
            inputListeners: function () {
              let vm = this;
              // `Object.assign` merges objects together to form a new object
              return Object.assign({},
                // We add all the listeners from the parent
                this.$listeners,
                // Then we can add custom listeners or override the
                // behavior of some listeners.
                {
                  // This ensures that the component works with v-model
                  input: function (event) {
                      event.target.blur();
                      vm.$emit('input', event.target.value)
                  }
                }
              )
            }
        },
    }
</script>
