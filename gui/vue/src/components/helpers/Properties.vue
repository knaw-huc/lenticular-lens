<template>
  <div>
    <div class="property" v-for="propAndValues in properties" v-if="propAndValues.values.length > 0">
      <div class="property-pill property-prop read-only sm">
        {{ propAndValues.property[propAndValues.property.length - 1] }}
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
