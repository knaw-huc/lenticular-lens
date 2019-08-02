<template>
  <sub-card>
    <div class="row ml-4" v-for="(property, idx) in properties" v-bind:class="{'mt-3': idx === 0}">
      <property
          v-if="property[0]"
          :property="property"
          :singular="true"
          :singular-resource-info="true"
          :follow-referenced-collection="false"
          @resetProperty="resetProperty(idx, property, $event)"/>
    </div>
  </sub-card>
</template>

<script>
    import SubCard from "../structural/SubCard";

    export default {
        name: "Properties",
        components: {
            SubCard,
        },
        props: {
            properties: Array,
        },
        methods: {
            resetProperty(idx, property, propertyIndex) {
                const newProperty = property.slice(0, propertyIndex);
                newProperty.push('');

                if (newProperty.length % 2 > 0)
                    newProperty.push('');

                this.$set(this.properties, idx, newProperty);
            },
        },
    }
</script>