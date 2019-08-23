<template>
  <div class="border p-4 mt-4 bg-light" v-bind:class="{'is-invalid': hasError}">
    <div class="sticky-top bg-light py-2" v-bind:class="showContent ? 'border-bottom' : {}">
      <div class="row flex-nowrap align-items-center justify-content-between">
        <div class="col-auto">
          <fa-icon icon="chevron-down" size="2x" v-b-toggle="id"></fa-icon>
        </div>

        <div class="flex-shrink-1" v-bind:class="[{'mr-auto': fillLabel}, isEditing ? 'col' : 'col-auto']">
          <input v-if="isEditing" type="text" class="form-control border-0" :value="value" ref="editInput" required
                 @blur="editing = false" @input="$emit('input', $event.target.value)"/>

          <div v-else-if="!label" class="row" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <div class="h2 col" v-b-toggle="id">{{ value }}</div>

            <button type="button" class="btn col-auto p-0" title="Click to Edit"
                    v-bind:class="{'invisible': !hovering}" @click="editing = true">
              <fa-icon icon="pencil-alt" size="lg"/>
            </button>
          </div>

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
                editing: false,
                hovering: false,
                showContent: false
            };
        },
        computed: {
            isEditing() {
                return !this.label && (this.editing || this.value === '');
            }
        },
        updated() {
            if (this.editing)
                this.$refs.editInput.focus();
        },
    };
</script>

<style scoped>
  input[type="text"] {
    font-size: 2rem;
    height: 2.5rem;
    box-shadow: none;
  }
</style>
