<template>
  <div>
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <h2>{{ title }}</h2>
      </div>

      <slot name="header"></slot>
    </div>

    <slot></slot>

    <b-alert :show="is_saved && tab_error !== ''" variant="warning" class="mt-4 mb-0">
      Successfully saved, but with errors:
      {{ tab_error }}
    </b-alert>

    <b-alert :show="!is_saved && tab_error !== ''" variant="danger" class="mt-4 mb-0">
      {{ tab_error }}
    </b-alert>
  </div>
</template>

<script>
    export default {
        name: 'TabContentStructure',
        props: {
            title: String,
            tab_error: String,
            is_saved: Boolean,
        },
    };
</script>