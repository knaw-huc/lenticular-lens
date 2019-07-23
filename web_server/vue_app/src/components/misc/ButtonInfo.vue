<template>
  <div class="btn-info-popup">
    <a class="btn btn-block text-info pt-1" @click="$refs['info_' + uuid].show()">
      <octicon name="question" :scale="scale"/>
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
            scale: {
                type: Number,
                default: 1.5,
            },
        },
    }
</script>

<style>
  .btn-info-popup a.btn.disabled,
  fieldset:disabled .btn-info-popup a.btn {
    pointer-events: auto;
  }
</style>