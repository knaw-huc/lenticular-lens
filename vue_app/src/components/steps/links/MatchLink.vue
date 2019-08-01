<template>
  <div class="row">
    <div class="col"> {{ link[0] }}</div>
    <div class="col"> {{ link[1] }}</div>
    <div class="col"> {{ link[2] }}</div>
  </div>
</template>

<script>
    export default {
        name: "MatchLink",
        props: {
            link: Array
        },
    }
</script>
