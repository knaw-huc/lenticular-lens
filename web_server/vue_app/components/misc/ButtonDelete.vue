<template>
    <button type="button" class="btn text-danger" :title="title" @click="$emit('click')">
        <octicon name="trashcan" :scale="scale"/>
    </button>
</template>

<script>
    export default {
        props: {
            scale: {
                type: [Number, String],
                default: 1,
            },
            title: String,
        },
    }
</script>
