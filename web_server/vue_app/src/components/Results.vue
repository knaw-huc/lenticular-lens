<template>
  <div class="container-fluid" id="app">
    <h1>Linksets created by alignment mapping "{{ mapping_name }}" ({{ rows_total }} total)</h1>
    <div v-if="rows.length > 0" class="row">
      <div v-for="(value, col_name) in rows[0]" class="col font-weight-bold pb-2">
        {{ col_name }}
      </div>
      <slot v-for="(row) in rows">
        <div class="w-100"></div>
        <div v-for="(value) in row" class="col" style="overflow: hidden;">
          {{ value }}
        </div>
      </slot>
    </div>
  </div>
</template>

<script>
    export default {
        name: "Results",
        data() {
            return {
                mapping_name: '',
                rows: [],
                rows_total: '',
            }
        },
        methods: {
            getRows() {
                fetch(window.location.href,
                    {
                        headers: {
                            'Accept': 'application/json',
                        },
                    })
                    .then((response) => response.json())
                    .then((data) => {
                        this.mapping_name = data.mapping_name;
                        this.rows = data.rows;
                        this.rows_total = data.rows_total;
                    });
            },
        },
        mounted() {
            this.getRows();
        },
    }
</script>