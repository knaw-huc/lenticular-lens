<template>
    <button
            type="button"
            :class="'btn btn-outline-info rounded-circle' + (scale < 1 ? ' pt-1 pb-1' : '')"
            :title="title"
            @click="handleBtnClick"
            ref="button"
    >
        <octicon name="plus" :scale="scale"/>
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
                default: 1,
            },
            title: String,
        },
    }
</script>