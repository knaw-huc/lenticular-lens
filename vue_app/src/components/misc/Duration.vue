<template>
  <span v-if="until">{{ momentDuration | duration('humanize') }} ({{ exactDuration }})</span>
  <span v-else>{{ momentDuration | duration('humanize', true) }}</span>
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
        computed: {
            momentDuration() {
                return this.until
                    ? this.$moment.duration(this.until.getTime()).subtract(this.from.getTime())
                    : this.$moment.duration(this.now.getTime()).subtract(this.from.getTime());
            },

            exactDuration() {
                const hours = this.momentDuration.hours();
                const minutes = this.momentDuration.minutes();
                const seconds = this.momentDuration.seconds();

                const hoursStr = String(hours).padStart(2, '0');
                const minutesStr = String(minutes).padStart(2, '0');
                const secondsStr = String(seconds).padStart(2, '0');

                if (hours > 0)
                    return `${hoursStr}:${minutesStr}:${secondsStr}`;

                if (minutes > 0)
                    return `00:${minutesStr}:${secondsStr}`;

                return `00:00:${secondsStr}`;
            },
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