<template>
    <div class="row pl-3">
        <property-component-component
                v-for="(n, index) in property.length"
                v-if="index % 2 === 0"
                :value="property.slice(index, index + 2)"
                :resources="getResourcesForIndex(index)"
                :properties="index === 0 ? dataset[resource.collection_id] : dataset[property[index]]"
                :singular="singular"
                @input="updateProperty($event, index)"
                @reset="$emit('resetProperty', index + $event)"
                @delete="$emit('delete')"
                @clone="$emit('clone')"
                ref="propertyComponents"
        ></property-component-component>
    </div>
</template>

<script>
    import PropertyComponent from "./PropertyComponent";
    export default {
        components: {'property-component-component': PropertyComponent},
        computed: {
            resource() {
                return this.$root.$children[0].getResourceById(this.property[0])
            },
            dataset() {
                return this.$root.$children[0].datasets[this.resource.dataset_id].collections
            },
        },
        methods: {
            validateProperty() {
                return !this.$refs.propertyComponents
                    .map(propertyComponent => propertyComponent.validatePropertyComponent())
                    .includes(false);
            },

            getResourcesForIndex(index) {
                if (index === 0)
                    return this.$root.$children[0].resources;

                let collection_id = index > 2 ? this.property[index - 2] : this.resource.collection_id;

                return this.dataset[collection_id][this.property[index - 1]]['referencedCollections']
            },
            updateProperty(input_value, ref_index) {
                this.$set(this.property, ref_index + input_value[0], input_value[1]);
                let collection_id = this.property.length > 2 ? this.property.slice(-2)[0] : this.resource.collection_id;

                if (this.property.slice(-1)[0] && Object.keys(this.$root.$children[0].getOrCreate(this.dataset[collection_id][this.property.slice(-1)[0]], 'referencedCollections', [])).length > 0) {
                    this.property.push('', '');
                }
            },
        },
        props: {
            property: Array,
            singular: {
                type: Boolean,
                default: false,
            },
        },
    }
</script>
