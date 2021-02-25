<template>
  <div>
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <h2>{{ title }}</h2>
      </div>

      <slot name="header"></slot>
    </div>

    <slot></slot>

    <div v-show="isSaved && tabError !== ''" class="alert alert-warning mt-4 mb-0" role="alert">
      Successfully saved, but with errors:
      {{ tabError }}
    </div>

    <div v-show="!isSaved && tabError !== ''" class="alert alert-danger mt-4 mb-0" role="alert">
      {{ tabError }}
    </div>
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