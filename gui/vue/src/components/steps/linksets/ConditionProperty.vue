<template>
  <div class="ml-5 p-3" v-bind:class="{'border-top': !isFirst}">
    <property :entity-type-selection="$root.getEntityTypeSelectionById(conditionProperty.entity_type_selection)"
              :property="conditionProperty.property" :allow-delete="allowDelete"
              @clone="$emit('clone')" @delete="$emit('delete')" ref="propertyComponent"/>

    <div class="row align-items-top mt-2">
      <div class="col-auto h5">Transformers</div>

      <div class="col-auto p-0 pb-1">
        <button-add @click="addTransformer" size="sm" title="Add Transformer" class="btn-sm"/>
      </div>

      <div class="col-auto">
        <div v-for="(transformer, idx) in conditionProperty.transformers" class="row align-items-center mb-1">
          <div class="col-auto pr-0 form-inline">
            <select-box v-model="transformer.name" @input="handleTransformerIndexChange(transformer)"
                        v-bind:class="{'is-invalid': errors.includes(`transformer_${idx}`)}">
              <option disabled selected value="">Select a transformer</option>
              <option v-for="(obj, name) in transformers" :value="name">{{ obj.label }}</option>
            </select-box>

            <div class="invalid-feedback inline-feedback ml-2" v-show="errors.includes(`transformer_${idx}`)">
              Please specify a transformer or remove the transformer
            </div>
          </div>

          <div v-if="getTransformerTemplate(transformer).items.length > 0" class="col-auto pr-0 form-inline">
            <template v-for="item in getTransformerTemplate(transformer).items">
              <label class="small mr-2" v-if="item.label">
                {{ item.label }}
              </label>

              <input class="form-control form-control-sm mr-2" v-model="transformer.parameters[item.key]"
                     v-bind:class="{'is-invalid': errors.includes(`transformer_value_${idx}_${item.key}`)}">

              <div class="invalid-feedback inline-feedback"
                   v-show="errors.includes(`transformer_value_${idx}_${item.key}`)">
                Please specify a valid value
              </div>
            </template>
          </div>

          <div class="col-auto p-0 pb-1 ml-2">
            <button-delete @click="conditionProperty.transformers.splice(idx, 1)" size="sm" class="btn-sm"/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import props from "../../../utils/props";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "ConditionProperty",
        mixins: [ValidationMixin],
        data() {
            return {
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
            };
        },
        props: {
            conditionProperty: Object,
            allowDelete: {
                type: Boolean,
                default: true,
            },
            isFirst: {
                type: Boolean,
                default: false,
            },
        },
        methods: {
            validateConditionProperty() {
                const propertyValid = this.$refs.propertyComponent.validateProperty();

                if (!this.conditionProperty.hasOwnProperty('transformers'))
                    this.conditionProperty.transformers = [];

                let transformersValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('transformer_'));
                this.conditionProperty.transformers.forEach((transformer, idx) => {
                    if (!this.validateField(`transformer_${idx}`, transformer.name && transformer.name.length > 0)) {
                        transformersValid = false;
                    }
                    else {
                        this.getTransformerTemplate(transformer).items.forEach(transformerItem => {
                            const field = `transformer_value_${idx}_${transformerItem.key}`;
                            const value = transformer.parameters[transformerItem.key];
                            if (!this.validateField(field, transformerItem.allowEmptyValue || (value && value.length > 0)))
                                transformersValid = false;
                        });
                    }
                });

                return propertyValid && transformersValid;
            },

            addTransformer(name = '') {
                this.conditionProperty.transformers.push({name, parameters: {}});
            },

            getTransformerTemplate(transformer) {
                if (this.transformers.hasOwnProperty(transformer.name))
                    return this.transformers[transformer.name];

                return {label: '', items: []};
            },

            handleTransformerIndexChange(transformer) {
                transformer.parameters = {};
                this.getTransformerTemplate(transformer).items.forEach(valueItem => {
                    transformer.parameters[valueItem.key] = valueItem.defaultValue;
                });
            },
        },
    };
</script>