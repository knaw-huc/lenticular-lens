<template>
  <div class="property">
    <div class="property-pill property-prop read-only sm">
      {{ propertyLabel }}
    </div>

    <ul class="property-values inline-list">
      <li v-for="value in values">
        {{ value }}
      </li>
    </ul>
  </div>
</template>

<script>
    import {getPropertyInfo} from "@/utils/property";

    export default {
        name: "PropertyValues",
        props: {
            graphqlEndpoint: String,
            datasetId: String,
            collectionId: String,
            property: Array,
            values: Array,
        },
        computed: {
            dataset() {
                const datasets = this.$root.getDatasets(this.graphqlEndpoint);
                return datasets[this.datasetId];
            },

            props() {
                return getPropertyInfo(this.property, this.collectionId, this.dataset.collections);
            },

            propertyLabel() {
                const prop = this.props[this.props.length - 1];
                const propInfo = prop.properties[prop.property];
                return propInfo.shortenedUri ? (propInfo.isInverse ? '← ' : '') + propInfo.shortenedUri : prop.property;
            },
        },
    };
</script>
