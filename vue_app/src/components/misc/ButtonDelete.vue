<template>
  <button type="button" class="btn text-danger p-0" :title="title" @click="$emit('click')" ref="button">
    <fa-icon icon="trash-alt" :size="size"/>
  </button>
</template>

<script>
    export default {
        props: {
            size: {
                type: String,
                default: 'lg',
            },
            title: String,
        },
    }
</script>
