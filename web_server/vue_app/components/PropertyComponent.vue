<template>
    <div class="col-auto">
        <div class="row">
            <div v-if="!Array.isArray(resources) && value[0]" class="col-auto p-1">
                <octicon name="arrow-right" />
            </div>
            <div v-if="!value[0] || (Array.isArray(resources) && !singular) || (value[0] && !Array.isArray(resources))" class="form-group col-auto">
                <template v-if="!value[0]">
                    <v-select :value="value[0]" @input="updateInput($event, 0)"
                              v-bind:class="{'is-invalid': errors.includes('value')}">
                        <template v-if="Array.isArray(resources)">
                            <option v-for="collection in resources" :key="collection.id" :value="collection.id">{{ collection.label }}
                            </option>
                        </template>
                        <template v-else>
                            <option value="" disabled selected>Choose a referenced collection</option>
                            <option value="__value__">Value (do not follow reference)</option>
                            <option v-for="collection in Object.keys(resources)" :key="collection" :value="collection">{{ collection }}
                            </option>
                        </template>
                    </v-select>
                </template>
                <div v-else-if="Array.isArray(resources) && !singular" class="row">
                    <template v-if="!singular">
                        <div class="col-auto border border-info p-1 rounded-pill pl-2 pr-2 bg-white">
                            {{ $root.$children[0].datasets[$root.$children[0].getResourceById(value[0], resources).dataset_id].title }}
                        </div>
                        <div class="col-auto border border-info p-1 rounded-pill ml-2 mr-2 pl-2 pr-2 bg-white">
                            {{ $root.$children[0].getResourceById(value[0], resources).collection_id }}
                        </div>
                        <div class="col-auto ml-0 pl-0">
                            <button-add
                                    @click="$emit('clone')"
                                    :scale="0.8"
                                    title="Add another property for this Collection"/>
                            <button-delete @click="$emit('delete')" scale="1.3" title="Remove this property"/>
                        </div>
                    </template>
                </div>
                <div v-else-if="!Array.isArray(resources)" class="row">
                    <button type="button" class="btn-info btn col-auto mt-1 pb-0 pt-0 rounded-pill" @click="$emit('reset', 0)">
                        {{ value[0] }}
                    </button>
                </div>
            </div>
            <template v-if="value[0] && value[0] !== '__value__'">
                <div v-if="!Array.isArray(resources)" class="col-auto p-1">
                    <octicon name="arrow-right" />
                </div>
                <div class="form-group col-auto">
                    <div class="row">
                        <template v-if="!value[1]">
                            <v-select class="form-control col-auto" :value="value[1]" @input="updateInput($event, 1)"
                                      v-bind:class="{'is-invalid': errors.includes('value')}">
                                <option value="" selected disabled>Choose a property</option>
                                <option v-for="property_opt in Object.keys(properties)" :value="property_opt">{{ property_opt }}</option>
                            </v-select>
                        </template>
                        <button v-else type="button" class=" mt-1 col-auto btn-info btn pb-0 pt-0 rounded-pill" @click="$emit('reset', 1)">
                            {{ value[1] }}
                        </button>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>
<script>
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        methods: {
            validatePropertyComponent() {
                return this.validateField('value', (this.value[0] === '__value__') ||
                    (this.value.find(value => value === '') === undefined));
            },

            updateInput(new_value, index) {
                this.$emit('input', [index, new_value]);
            },
        },
        name: 'property-component-component',
        props: {
            properties: Object,
            resources: [Array, Object],
            singular: {
                type: Boolean,
                default: false,
            },
            value: Array,
        },
    }
</script>