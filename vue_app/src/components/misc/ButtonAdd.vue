<template>
  <button type="button" class="btn text-info p-0" :title="title" @click="handleBtnClick" ref="button">
    <fa-icon icon="plus" :size="size"/>
  </button>
</template>

<script>
    export default {
        methods: {
            handleBtnClick() {
                this.$refs['button'].blur();
                this.$emit('click');
            },
        },
        props: {
            size: {
                type: String,
                default: 'lg',
            },
            title: String,
        },
    }
</script>