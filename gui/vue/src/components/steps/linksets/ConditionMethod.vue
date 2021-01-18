<template>
  <div>
    <div v-for="(item, idx) in this.method.items"
         v-if="item.type !== 'property' || condition[configKey][item.entity_type_selection_key] !== undefined"
         class="form-group row">
      <label v-if="showLabel(item)" :for="id + idx" class="col-sm-3 col-form-label">{{ item.label }}</label>

      <div v-if="item.type === 'number'" class="col-sm-2">
        <input :id="id + idx" class="form-control form-control-sm" type="number"
               :step="item.step || 1" :min="item.minValue" :max="item.maxValue"
               v-model.number="condition[configKey][item.key]"
               v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}">

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify a valid value
        </div>
      </div>

      <div v-else-if="item.type === 'range'" class="col-sm-2">
        <range :id="id + idx" :step="item.step" :min="item.minValue" :max="item.maxValue"
               v-model.number="condition[configKey][item.key]"
               v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}"/>

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify a valid value
        </div>
      </div>

      <div v-else-if="item.type === 'string'" class="col-sm-3">
        <input :id="id + idx" class="form-control form-control-sm" type="text"
               v-model="condition[configKey][item.key]"
               v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}">

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify a valid value
        </div>
      </div>

      <div v-else-if="item.type === 'choices'" class="col-sm-3">
        <select :id="id + idx" class="form-control form-control-sm h-auto" v-model="condition[configKey][item.key]"
                v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}">
          <option disabled selected value="">Select an option</option>
          <option v-for="(choiceValue, choiceLabel) in item.choices" :value="choiceValue">
            {{ choiceLabel }}
          </option>
        </select>

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify a valid value
        </div>
      </div>

      <div v-else-if="item.type === 'boolean'" class="col">
        <div class="form-check">
          <input class="form-check-input" type="checkbox"
                 :id="id + idx" v-model="condition[configKey][item.key]"
                 v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}">

          <label class="form-check-label" :for="id + idx">
            {{ item.label }}
          </label>

          <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
            Please specify a valid value
          </div>
        </div>
      </div>

      <div v-else-if="item.type === 'entity_type_selection'" class="col-sm-6">
        <select :id="id + idx" class="form-control form-control-sm h-auto" v-model="condition[configKey][item.key]"
                v-bind:class="{'is-invalid': errors.includes(`method_config_${item.key}`)}">
          <option disabled selected value="">Choose an entity-type selection</option>
          <option v-for="ets in $root.entityTypeSelections" :value.number="ets.id">
            {{ ets.label }}
          </option>
        </select>

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify an entity-type selection
        </div>
      </div>

      <div v-else-if="item.type === 'property'" class="col-sm row align-items-center m-0 mb-1">
        <property
            :entity-type-selection="$root.getEntityTypeSelectionById(condition[configKey][item.entity_type_selection_key])"
            :property="condition[configKey][item.key]"
            :singular="true" :allow-delete="false" :entity-type-selection-info="false" :ref="item.key"/>

        <div class="invalid-feedback" v-show="errors.includes(`method_config_${item.key}`)">
          Please specify a property
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "ConditionMethod",
        mixins: [ValidationMixin],
        props: ['id', 'method', 'condition', 'configKey'],
        methods: {
            validateConditionMethod() {
                let methodValueValid = true;

                this.errors = this.errors.filter(err => !err.startsWith('method_config_'));
                this.method.items.forEach(valueItem => {
                    const value = this.condition[this.configKey][valueItem.key];

                    const valueValid = !this.isInvalidMinValue(valueItem, value)
                        && !this.isInvalidMaxValue(valueItem, value)
                        && !this.isInvalidChoices(valueItem, value)
                        && !this.isInvalidEntityTypeSelection(valueItem, value)
                        && !this.isInvalidProperty(valueItem, value);

                    if (!this.validateField(`method_config_${valueItem.key}`, valueValid))
                        methodValueValid = false;
                });

                return methodValueValid;
            },

            isInvalidMinValue(valueItem, value) {
                return (valueItem.type === 'number' || valueItem.type === 'range')
                    && valueItem.hasOwnProperty('minValue')
                    && (isNaN(parseFloat(value)) || (parseFloat(value) < valueItem.minValue));
            },

            isInvalidMaxValue(valueItem, value) {
                return (valueItem.type === 'number' || valueItem.type === 'range')
                    && valueItem.hasOwnProperty('maxValue')
                    && (isNaN(parseFloat(value)) || (parseFloat(value) > valueItem.maxValue));
            },

            isInvalidChoices(valueItem, value) {
                return valueItem.type === 'choices' && !Object.values(valueItem.choices).includes(value);
            },

            isInvalidEntityTypeSelection(valueItem, value) {
                return valueItem.type === 'entity_type_selection' && !value;
            },

            isInvalidProperty(valueItem, value) {
                return valueItem.type === 'property' && (!value || value.length === 0)
                    && !this.$refs[valueItem.key].validateProperty();
            },

            showLabel(item) {
                return item.label && item.type !== 'boolean' && (item.type !== 'property'
                    || this.condition[this.configKey][item.entity_type_selection_key] !== undefined);
            },
        },
    };
</script>