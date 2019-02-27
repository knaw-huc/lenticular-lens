<template>
    <div class="col">
        <div class="row">
            <div class="form-group col-4">
                <select class="form-control" :value="value[value_index]" @input="updateInput($event.target.value, value_index)">
                    <template v-if="Array.isArray(resources)">
                        <option v-for="collection in resources" :key="collection.id" :value="collection.id">{{ collection.label }}
                        </option>
                    </template>
                    <template v-else>
                        <option v-for="collection in Object.keys(resources)" :key="collection" :value="collection">{{ collection }}
                        </option>
                    </template>
                </select>
            </div>
            ::
            <div class="form-group col-4">
                <select class="form-control" :value="value[value_index + 1]" @input="updateInput($event.target.value, value_index + 1)">
                    <option value="" selected disabled>Choose a property</option>
                    <option v-for="property_opt in Object.keys(properties)" :value="property_opt">{{ property_opt }}</option>
                </select>
            </div>
        </div>
        <template v-if="value[value_index + 1] && properties[value[value_index + 1]]['referencedCollections'] && Object.keys(properties[value[value_index + 1]]['referencedCollections']).length > 0">
            <div class="row">
                -->
                <property-component
                        v-model="value"
                        :value_index="value_index + 2"
                        :resources="properties[value[value_index + 1]]['referencedCollections']"
                ></property-component>
            </div>
        </template>
    </div>
</template>
<script>
    export default {
        computed: {
            properties() {
                if (Array.isArray(this.resources)) {
                    return this.$parent.properties;
                } else {
                    return this.value[this.value_index] ? this.resources[this.value[this.value_index]] : []
                }
            },
        },
        methods: {
            updateInput(new_value, index) {
                this.$set(this.value, index, new_value);
                this.$emit('input', this.value);
            },
        },
        name: 'property-component',
        props: {
            value_index: 0,
            resources: [Array, Object],
            value: Array,
        },
    }
</script>