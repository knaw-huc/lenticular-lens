<template>
    <button type="button" class="btn text-danger" :title="title" @click="handleBtnClick" ref="button">
        <octicon name="trashcan" :scale="scale"/>
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
            scale: {
                type: [Number, String],
                default: 2,
            },
            title: String,
        },
    }
</script>
