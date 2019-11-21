<template>
  <div>
    <div class="property" v-for="propAndValues in properties">
      <div class="property-resource property-pills">
        <div class="property-pill sm read-only">
          {{ propAndValues.property }}
        </div>
      </div>

      <ul class="property-values inline-list">
        <li v-for="value in propAndValues.values">
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
    };
</script>
