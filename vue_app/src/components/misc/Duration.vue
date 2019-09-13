<template>
  <span v-if="until">{{ from | duration('add', until) | duration('humanize') }}</span>
  <span v-else>{{ from | duration('add', now) | duration('humanize', true) }}</span>
</template>

<script>
    export default {
        props: {
            from: Date,
            until: Date,
        },
        data() {
            return {
                now: new Date(),
            };
        },
        methods: {
            updateNow() {
                this.now = new Date();
            },
        },
        created() {
            setInterval(this.updateNow, 1000);
        },
        destroyed() {
            clearInterval(this.updateNow);
        },
    };
</script>