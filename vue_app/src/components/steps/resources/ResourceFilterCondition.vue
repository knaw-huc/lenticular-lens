<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between m-0 mb-2">
      <div class="col">
        <property :property="condition.property" :singular="true" :resource-info="false"
                  @resetProperty="resetProperty(condition.property, $event)" ref="propertyComponent"/>
      </div>

      <div class="col-auto">
        <div class="row">
          <div class="col-auto">
            <button-delete @click="$emit('remove', index)" title="Delete this Filter Condition" class="pt-1 pr-0"/>
          </div>

          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Filter Condition and Create Group"/>
          </div>
        </div>
      </div>
    </div>

    <div class="form-row align-items-center">
      <div class="col-3">
        <select-box :auto-height="false" v-model="condition.type"
                    v-bind:class="{'is-invalid': errors.includes('condition')}">
          <option value="" disabled selected>Choose a filter type</option>
          <option value="=">Equal to</option>
          <option value="!=">Not equal to</option>
          <option value="is_null">Has no value</option>
          <option value="not_null">Has a value</option>
          <option value="date_is_within">Date is within</option>
          <option value="date_is_not_within">Date is not within</option>
          <option value="ilike">Contains (use % for wildcard)</option>
          <option value="not_ilike">Does not contain (use % for wildcard)</option>
          <option value="appearances">Appearances of property</option>
        </select-box>
      </div>

      <div v-if="requiresValue" class="col-3">
        <input class="form-control form-control-sm" type="text" v-model="condition.value" placeholder="Enter a value"
               v-bind:class="{'is-invalid': errors.includes('value')}">
      </div>

      <div v-if="condition.type === 'appearances'" class="col-2">
        <select-box :auto-height="false" v-model="condition.operator">
          <option value="<=" selected>Max.</option>
          <option value=">=" selected>Min.</option>
          <option value="=" selected>Exactly</option>
        </select-box>
      </div>

      <div v-if="condition.type === 'appearances'" class="col-1">
        <input class="form-control form-control-sm" type="number" min="0" step="1" v-model.number="condition.value"
               v-bind:class="{'is-invalid': errors.includes('value')}">
      </div>
    </div>

    <div class="row" v-show="errors.includes('property') || errors.includes('condition') || errors.includes('value')">
      <div class="invalid-feedback d-block pl-3">
        <template v-if="errors.includes('property')">
          Please select a property
        </template>

        <template v-if="errors.includes('property') && (errors.includes('condition') || errors.includes('value'))">
          <br/>
        </template>

        <template v-if="errors.includes('condition')">
          Please provide a filter type
        </template>
        <template v-else-if="errors.includes('value') && condition.type === 'appearances'">
          Please provide a number for the condition
        </template>
        <template v-else-if="errors.includes('value')">
          Please provide a value for the condition
        </template>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "ResourceFilterCondition",
        mixins: [ValidationMixin],
        props: ['resource', 'condition', 'index'],
        computed: {
            requiresValue() {
                return ['=', '!=', 'date_is_within', 'date_is_not_within', 'ilike', 'not_ilike']
                    .includes(this.condition.type);
            },
        },
        methods: {
            validateFilterCondition() {
                const propertyValid = this.validateField('property', this.$refs.propertyComponent.validateProperty());
                const conditionValid = this.validateField('condition', this.condition.type);

                let valueValid = false;
                if (this.requiresValue)
                    valueValid = this.validateField('value', this.condition.value);
                else if (this.condition.type === 'appearances')
                    valueValid = this.validateField('value', !isNaN(parseInt(this.condition.value))
                        && parseInt(this.condition.value) > 0);
                else
                    valueValid = this.validateField('value', true);

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
    }
</script>
