<template>
  <tr>
    <td> {{ link[0] }}</td>
    <td> {{ link[1] }}</td>
    <td> {{ link[2] }}</td>
  </tr>
</template>

<script>
    export default {
        name: "LinksTableRow",
        props: {
            link: Array
        },
    }
</script>

<style scoped>
  tr {
    width: 100%;
    display: flex;
  }

  td {
    display: flex;
    flex: 1;
    align-items: center;
  }
</style>