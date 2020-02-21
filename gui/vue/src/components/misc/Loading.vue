<template>
  <div class="d-flex justify-content-center">
    <div class="spinner-border text-info" role="status" v-bind:class="small ? 'small-spinner' : 'big-spinner'">
      <span class="sr-only">Loading...</span>
    </div>
  </div>
</template>

<script>
    export default {
        props: {
            small: false
        },
    }
</script>

<style>
  .big-spinner {
    width: 3rem;
    height: 3rem;
  }

  .small-spinner {
    width: 1.5rem;
    height: 1.5rem;
  }
</style>