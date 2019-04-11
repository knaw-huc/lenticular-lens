<template>
    <button
            type="button"
            :class="'btn btn-outline-info rounded-circle' + (scale < 1 ? ' pt-1 pb-1' : '')" :title="title" @click="$emit('click')"
    >
        <octicon name="plus" :scale="scale"/>
    </button>
</template>

<script>
    export default {
        props: {
            scale: {
                type: Number,
                default: 1,
            },
            title: String,
        },
    }
</script>