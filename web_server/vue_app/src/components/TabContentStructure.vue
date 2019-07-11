<template>
  <div>
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <h2>{{ title }}</h2>
      </div>

      <slot name="header"></slot>
    </div>

    <slot></slot>

    <b-alert variant="danger" class="mt-4" :show="tab_error !== ''">
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
        },
    };
</script>