<template>
  <div v-if="editing || value === ''" class="form-group col-auto">
    <input type="text" class="form-control border-0" :value="value" @blur="editing = false" ref="editInput"
           @input="$emit('input', $event.target.value)" :required="required">
  </div>

  <div v-else class="row" @mouseenter="hovering = true" @mouseleave="hovering = false">
    <div class="h2 col">{{ value }}</div>
    <button type="button" class="btn col-auto pl-0 pt-0" title="Click to Edit">
      <octicon name="pencil" scale="1.2" :class="hideClass" @click.native.stop.prevent="editing = true"/>
    </button>
  </div>
</template>

<script>
    export default {
        name: 'EditLabel',
        data() {
            return {
                editing: false,
                hovering: false,
            }
        },
        props: {
            value: String,
            required: Boolean,
        },
        computed: {
            hideClass() {
                return this.hovering ? '' : ' invisible';
            },
        },
        updated() {
            if (this.editing)
                this.$refs.editInput.focus();
        },
    }
</script>

<style scoped>
  input[type="text"] {
    font-size: 2rem;
    height: 2.5rem;
    box-shadow: none;
  }
</style>
