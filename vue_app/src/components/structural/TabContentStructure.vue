<template>
  <div>
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <h2>{{ title }}</h2>
      </div>

      <slot name="header"></slot>
    </div>

    <slot></slot>

    <b-alert :show="isSaved && tabError !== ''" variant="warning" class="mt-4 mb-0">
      Successfully saved, but with errors:
      {{ tabError }}
    </b-alert>

    <b-alert :show="!isSaved && tabError !== ''" variant="danger" class="mt-4 mb-0">
      {{ tabError }}
    </b-alert>
  </div>
</template>

<script>
    export default {
        name: 'TabContentStructure',
        props: {
            title: String,
            tabError: String,
            isSaved: Boolean,
        },
    };
</script>