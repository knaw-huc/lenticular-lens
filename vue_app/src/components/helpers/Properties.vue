<template>
  <div>
    <div class="property" v-for="(values, property) in propsGrouped">
      <div class="property-resource property-pills">
        <div class="property-pill sm read-only">
          {{ property }}
        </div>
      </div>

      <ul class="property-values inline-list">
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
