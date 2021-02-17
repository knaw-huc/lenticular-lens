<template>
  <span v-if="until">
    {{ momentDuration | duration('humanize') }}
    <span class="font-italic">({{ exactDuration }})</span>
  </span>
  <span v-else>
    {{ momentDuration | duration('humanize', true) }}
  </span>
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
                const from = this.$moment(this.from.getTime());
                const until = this.$moment(this.until ? this.until.getTime() : this.now.getTime());

                return this.$moment.duration(from.diff(until));
            },

            exactDuration() {
                const days = Math.abs(this.momentDuration.days());
                const hours = Math.abs(this.momentDuration.hours());
                const minutes = Math.abs(this.momentDuration.minutes());
                const seconds = Math.abs(this.momentDuration.seconds());

                const hoursStr = String(hours).padStart(2, '0');
                const minutesStr = String(minutes).padStart(2, '0');
                const secondsStr = String(seconds).padStart(2, '0');

                const prefix = days > 0 ? `${days} ${days === 1 ? 'day' : 'days'} and ` : '';

                if (hours > 0)
                    return `${prefix}${hoursStr}:${minutesStr}:${secondsStr}`;

                if (minutes > 0)
                    return `${prefix}00:${minutesStr}:${secondsStr}`;

                return `${prefix}00:00:${secondsStr}`;
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