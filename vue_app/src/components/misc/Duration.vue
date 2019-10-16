<template>
  <span v-if="until">{{ from.getTime() | duration('subtract', until.getTime()) | duration('humanize') }}</span>
  <span v-else>{{ from.getTime() | duration('subtract', now.getTime()) | duration('humanize', true) }}</span>
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