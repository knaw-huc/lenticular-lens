<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between m-0 mb-2">
      <div class="col p-0">
        <ets-property :entity-type-selection="entityTypeSelection" :property="condition.property"
                      :singular="true" :entity-type-selection-info="false" ref="propertyComponent"/>
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
        <select-box :auto-height="false" v-model="condition.type" @input="onTypeSelection"
                    v-bind:class="{'is-invalid': errors.includes('condition')}">
          <option value="" disabled selected>Choose a filter type</option>
          <option value="equals">Equal to</option>
          <option value="not_equals">Not equal to</option>
          <option value="empty">Has no value</option>
          <option value="not_empty">Has a value</option>
          <option value="contains">Contains</option>
          <option value="not_contains">Does not contain</option>
          <option value="minimal">Has minimal value</option>
          <option value="maximum">Has maximum value</option>
          <option value="minimal_date">Has minimal date</option>
          <option value="maximum_date">Has maximum date</option>
          <option value="minimal_appearances">Has minimal appearances</option>
          <option value="maximum_appearances">Has maximum appearances</option>
        </select-box>
      </div>

      <div v-if="requiresStringValue" class="col-3">
        <input class="form-control form-control-sm" type="text" v-model="condition.value"
               placeholder="Enter a value" v-bind:class="{'is-invalid': errors.includes('value')}">
      </div>
      <div v-else-if="requiresIntegerValue" class="col-1">
        <input class="form-control form-control-sm" type="number" v-model.number="condition.value"
               placeholder="Enter a value" v-bind:class="{'is-invalid': errors.includes('value')}">
      </div>

      <div v-if="condition.type === 'minimal_date' || condition.type === 'maximum_date'" class="col-4 form-inline">
        <label>
          Date format
          <input class="form-control form-control-sm ml-2" v-model="condition.format" value="YYYY-MM-DD"
                 v-bind:class="{'is-invalid': errors.includes('format')}">
        </label>
      </div>
    </div>

    <div v-if="condition.type === 'ilike' || condition.type === 'not_ilike'" class="row">
      <small class="form-text text-muted pl-3">
        Use % as a wildcard character
      </small>
    </div>
    <div v-else-if="condition.type === 'minimal_date' || condition.type === 'maximum_date'" class="row">
      <small class="form-text text-muted pl-3">
        Use the format YYYY-MM-DD, YYYY-MM or YYYY for year/month/day, year/month and year respectively
      </small>
    </div>

    <div class="row" v-show="errors.includes('property') || hasConditionErrors">
      <div class="invalid-feedback pl-3"
           v-bind:class="{'is-invalid': errors.includes('property') || hasConditionErrors}">
        <template v-if="errors.includes('property')">
          Please select a property
        </template>

        <template v-if="errors.includes('property') && hasConditionErrors">
          <br/>
        </template>

        <template v-if="errors.includes('condition')">
          Please provide a filter type
        </template>
        <template v-else-if="errors.includes('value')">
          Please provide a value for the condition
        </template>
        <template v-else-if="errors.includes('format')">
          Please provide a date format
        </template>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "FilterCondition",
        mixins: [ValidationMixin],
        props: {
            entityTypeSelection: Object,
            condition: Object,
            index: Number,
        },
        computed: {
            requiresStringValue() {
                return [
                    'equals', 'not_equals', 'minimal_date', 'maximum_date', 'contains', 'not_contains'
                ].includes(this.condition.type);
            },

            requiresIntegerValue() {
                return [
                    'minimal', 'maximum', 'minimal_appearances', 'maximum_appearances'
                ].includes(this.condition.type);
            },

            hasConditionErrors() {
                return this.errors.includes('condition')
                    || this.errors.includes('value')
                    || this.errors.includes('format');
            },
        },
        methods: {
            validateFilterCondition() {
                const propertyValid = this.validateField('property', this.$refs.propertyComponent.validateProperty());
                const conditionValid = this.validateField('condition', this.condition.type);

                let valueValid = this.validateField('value', true);
                if (this.requiresStringValue || this.requiresIntegerValue)
                    valueValid = this.validateField('value', this.condition.value);

                const formatValid = this.validateField('format', this.condition.format
                    || (this.condition.type !== 'minimal_date' && this.condition.type !== 'maximum_date'));

                return propertyValid && conditionValid && valueValid && formatValid;
            },

            onTypeSelection() {
                if (!this.condition.format &&
                    (this.condition.type === 'minimal_date' || this.condition.type === 'maximum_date'))
                    this.condition.format = 'YYYY-MM-DD';
                else if (this.condition.type !== 'minimal_date' && this.condition.type !== 'maximum_date')
                    delete this.condition.format;

                if (this.requiresStringValue && this.condition.value)
                    this.condition.value = String(this.condition.value);
                else if (this.requiresIntegerValue && this.condition.value) {
                    if (!isNaN(parseInt(this.condition.value)))
                        this.condition.value = parseInt(this.condition.value);
                    else
                        delete this.condition.value;
                }
                else
                    delete this.condition.value;
            },
        },
    }
</script>
