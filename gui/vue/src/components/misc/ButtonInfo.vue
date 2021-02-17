<template>
  <div class="btn-secondary-popup">
    <a class="btn btn-block text-secondary py-0" @click="$refs['info_' + uuid].show()">
      <fa-icon :icon="['far', 'question-circle']" size="lg"/>
    </a>

    <b-modal
        :id="'info_' + uuid"
        :ref="'info_' + uuid"
        :title="popup_title"
        :size="popup_size"
        scrollable
        class="text-center"
        hide-footer
        :return-focus="$root.$children[0].$el">
      <slot></slot>
    </b-modal>
  </div>
</template>

<script>
    let uuid = 0;

    export default {
        beforeCreate() {
            this.uuid = uuid.toString();
            uuid++;
        },
        props: {
            popup_size: {
                type: String,
                default: 'xl',
            },
            popup_title: String,
        },
    }
</script>

<style>
  .btn-secondary-popup a.btn.disabled,
  fieldset:disabled .btn-secondary-popup a.btn {
    pointer-events: auto;
  }
</style>