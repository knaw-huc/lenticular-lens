<template>
  <div>
    <div class="row m-0" v-for="(values, property) in propsGrouped">
      <div class="col-auto p-0">
        <div class="property-path btn-sm read-only">
          {{ property }}
        </div>
      </div>

      <ul class="col-auto text-info text-break-all p-0 mb-0 mt-1 ml-2">
        <li v-for="value in values">
          {{ value }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
    export default {
        name: "Properties",
        props: {
            properties: Array
        },
        computed: {
            propsGrouped() {
                return this.properties.reduce((acc, propAndValues) => {
                    if (!acc.hasOwnProperty(propAndValues.property[1]))
                        acc[propAndValues.property[1]] = [];

                    acc[propAndValues.property[1]].push(...propAndValues.values);
                    return acc;
                }, {});
            }
        },
    };
</script>

<style scoped>
  ul {
    list-style: none;
  }
</style>
