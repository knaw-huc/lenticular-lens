<template>
  <div class="d-flex justify-content-center text-danger">
    <fa-icon icon="times" :size="size"/>
  </div>
</template>


<script>
    export default {
        props: {
            size: {}
        },
    }
</script>