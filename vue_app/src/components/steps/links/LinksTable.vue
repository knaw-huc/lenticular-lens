<template>
  <div class="links_result bg-white border mt-4">
    <table class="table table-striped">
      <thead>
      <tr>
        <th>Source</th>
        <th>Target</th>
        <th>Strength</th>
      </tr>
      </thead>
      <tbody>
      <links-table-row v-for="(link, idx) in links" :key="idx" :link="link"/>
      </tbody>
    </table>
  </div>
</template>

<script>
    import LinksTableRow from "./LinksTableRow";

    export default {
        name: "LinksTable",
        components: {
            LinksTableRow,
        },
        props: {
            links: Array,
        }
    }
</script>

<style>
  .links_result {
    height: 20em;
  }

  .links_result table {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .links_result table thead {
    margin-right: 15px;
  }

  .links_result table tbody {
    overflow-y: scroll;
  }

  .links_result table tr {
    width: 100%;
    display: flex;
  }

  .links_result table th {
    display: flex;
    flex: 1;
    align-items: center;
  }

  .links_result table th,
  .links_result table td {
    border: none;
  }
</style>