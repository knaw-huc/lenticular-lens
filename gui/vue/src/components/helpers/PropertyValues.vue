<template>
  <div class="property">
    <span class="first-el"/>

    <div class="property-pill property-resource property-collapse hide read-only sm"
         :title="dataset.uri" v-bind:class="id">
      {{ dataset.title }}
    </div>

    <div class="property-pill property-resource property-collapse hide read-only sm"
         :title="collection.uri" v-bind:class="id">
      {{ getCollectionLabel(collection, collectionId) }}
    </div>

    <template v-for="(prop, idx) in props">
      <template v-if="prop.collections && (!isLastProp(idx) || hasProperty(prop))">
        <fa-icon icon="arrow-right" class="property-part property-collapse hide" v-bind:class="id"/>

        <div class="property-pill property-prop property-collapse hide read-only sm"
             :title="prop.collections[prop.collection].uri" v-bind:class="id">
          {{ getCollectionLabel(prop.collections[prop.collection], prop.collection) }}
        </div>
      </template>

      <template v-if="hasProperty(prop) && (!isLastProp(idx))">
        <fa-icon v-if="prop.collection" icon="arrow-right"
                 class="property-part property-collapse hide" v-bind:class="id"/>

        <div class="property-pill property-prop property-collapse hide read-only sm"
             :title="prop.properties[prop.property].uri" v-bind:class="id">
          {{ getPropertyLabel(prop.properties[prop.property], prop.property) }}
        </div>
      </template>

      <fa-icon v-if="isLastProp(idx)" icon="arrow-right"
               class="property-part property-collapse hide" v-bind:class="id"/>
    </template>

    <div v-if="lastProp.collections && !hasProperty(lastProp)"
         class="property-pill property-prop read-only sm" :title="lastProp.collections[lastProp.collection].uri">
      {{ getCollectionLabel(lastProp.collections[lastProp.collection], lastProp.collection) }}
    </div>

    <div v-else-if="hasProperty(lastProp)"
         class="property-pill property-prop read-only sm" :title="lastProp.properties[lastProp.property].uri">
      {{ getPropertyLabel(lastProp.properties[lastProp.property], lastProp.property) }}
    </div>

    <span class="property-part">
      <button type="button" class="property-collapse-close hide btn p-0" v-bind:class="id"
              title="Hide property path" @click="closePath" ref="button">
        <fa-icon icon="compress-alt"/>
      </button>

      <button type="button" class="property-collapse-open btn p-0" v-bind:class="id"
              title="Show property path" @click="openPath" ref="button">
        <fa-icon icon="expand-alt"/>
      </button>
    </span>

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

            collection() {
                return this.dataset.collections[this.collectionId];
            },

            props() {
                return getPropertyInfo(this.property, this.collectionId, this.dataset.collections);
            },

            lastProp() {
                return this.props[this.props.length - 1];
            },

            id() {
                const str = JSON.stringify(this.property);

                let hash = 0;
                for (let i = 0; i < str.length; i++) {
                    const char = str.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash;
                }

                return 'prop' + hash;
            },
        },
        methods: {
            hasProperty(prop) {
                return prop.properties && prop.property !== '__value__';
            },

            isLastProp(idx) {
                return idx === (this.props.length - 1);
            },

            getCollectionLabel(collection, collectionId) {
                return collection.title || collection.shortenedUri || collectionId;
            },

            getPropertyLabel(property, propertyId) {
                return property.shortenedUri ? (property.isInverse ? '← ' : '') + property.shortenedUri : propertyId;
            },

            openPath() {
                document.querySelectorAll('.property-collapse.' + this.id)
                    .forEach(elem => elem.classList.remove('hide'));
                document.querySelectorAll('.property-collapse-close.' + this.id)
                    .forEach(elem => elem.classList.remove('hide'));
                document.querySelectorAll('.property-collapse-open.' + this.id)
                    .forEach(elem => elem.classList.add('hide'));
            },

            closePath() {
                document.querySelectorAll('.property-collapse.' + this.id)
                    .forEach(elem => elem.classList.add('hide'));
                document.querySelectorAll('.property-collapse-close.' + this.id)
                    .forEach(elem => elem.classList.add('hide'));
                document.querySelectorAll('.property-collapse-open.' + this.id)
                    .forEach(elem => elem.classList.remove('hide'));
            },
        }
    };
</script>
