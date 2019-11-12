<template>
  <select class="form-control form-control-sm" v-on="inputListeners" v-bind="$attrs" :value="value">
    <slot/>
  </select>
</template>

<script>
    export default {
        inheritAttrs: false,
        props: ['value'],
        computed: {
            inputListeners: function () {
                return Object.assign({},
                    this.$listeners,
                    {
                        input: (event) => {
                            event.target.blur();
                            this.$emit('input', event.target.value);
                        }
                    }
                )
            }
        },
    }
</script>
