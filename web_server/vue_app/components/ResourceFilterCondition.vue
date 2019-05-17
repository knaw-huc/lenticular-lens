<template>
<div class="border border-dark p-3 mb-3">
    <div class="row justify-content-between">
        <div class="col-10">
            <div class="row">
                <div class="col-auto form-group mb-0">
                    <label>Property:</label>
                </div>
            </div>
            <property-component
                    :property="condition.property"
                    :singular="true"
                    @resetProperty="resetProperty(condition.property, $event)"
                    ref="propertyComponent"
            />
        </div>
        <div class="col-auto">
            <div class="row justify-content-end">
                <div class="form-group col-auto">
                    <button-delete @click="$emit('remove')" title="Delete this Filter Condition" class="pt-1 pr-0"/>
                </div>

                <div class="form-group col-auto">
                    <button-add v-on:click="$emit('add-condition')" title="Add Filter Condition and Create Group"/>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="form-group col-3">
            <v-select v-model="condition.type" v-bind:class="{'is-invalid': errors.includes('condition')}">
                <option value="" disabled selected>Choose a filter type</option>
                <option value="=">Equal to</option>
                <option value="!=">Not equal to</option>
                <option value="not_null">Is not null</option>
                <option value="date_is_within">date is within</option>
                <option value="appearances">appearances of property</option>
                <option value="ilike">Contains (use % for wildcard)</option>
            </v-select>
            <div class="invalid-feedback" v-show="errors.includes('condition')">
                Please provide a filter type
            </div>
        </div>

        <div v-if="['=', '!=', 'date_is_within', 'ilike'].indexOf(condition.type) > -1" class="form-group col-3">
            <input class="form-control" type="text" v-model="condition.value" placeholder="Enter a value"
                   v-bind:class="{'is-invalid': errors.includes('value')}">
            <div class="invalid-feedback" v-show="errors.includes('value')">
                Please provide a value for the condition
            </div>
        </div>

        <div v-if="condition.type == 'appearances'" class="form-group col-2">
            <v-select v-model="condition.operator">
                <option value="<=" selected>Max.</option>
                <option value=">=" selected>Min.</option>
                <option value="=" selected>Exactly</option>
            </v-select>
        </div>
        <div v-if="condition.type == 'appearances'" class="form-group col-1">
            <input class="form-control" type="number" min="0" step="1" v-model.number="condition.value"
                   v-bind:class="{'is-invalid': errors.includes('value')}">
            <div class="invalid-feedback" v-show="errors.includes('value')">
                Please provide a number for the condition
            </div>
        </div>

        <div class="form-check">
            <input v-model.boolean="condition.invert" type="checkbox" class="form-check-input" :id="'resource_' + resource.id + '_condition_' + index + '_invert'">
            <label class="form-check-label" :for="'resource_' + resource.id + '_condition_' + index + '_invert'">Invert</label>
        </div>
    </div>
</div>
</template>

<script>
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        computed: {
            datasets() {
                return this.$parent.datasets
            },
            properties() {
                return this.$parent.datasets[this.$parent.resource.dataset_id]['collections'][this.$parent.resource.collection_id];
            },
            resource() {
                return this.$parent.resource;
            },
        },
        methods: {
            validateFilterCondition() {
                const propertyValid = this.$refs.propertyComponent.validateProperty();

                const conditionValid = this.validateField('condition', this.condition.type);

                const valueValid = this.validateField('value', this.condition.value &&
                    (this.condition.type !== 'appearances' ||
                        (!isNaN(parseInt(this.condition.value)) && parseInt(this.condition.value) > 0)));

                return propertyValid && conditionValid && valueValid;
            },

            resetProperty(property, property_index) {
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(this.condition, 'property', new_property);
            },
        },
        props: ['condition', 'index'],
    }
</script>
