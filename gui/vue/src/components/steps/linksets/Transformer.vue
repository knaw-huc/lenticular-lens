<template>
  <div class="row align-items-center mb-1">
    <div class="col-auto p-0">
      <handle/>
    </div>

    <div class="col-auto pr-0 form-inline">
      <select-box v-model="transformer.name" @input="handleTransformerIndexChange()"
                  v-bind:class="{'is-invalid': errors.includes('transformer')}">
        <option disabled selected value="">Select a transformer</option>
        <option v-for="(obj, name) in availableTransformers" :value="name">{{ obj.label }}</option>
      </select-box>

      <div class="invalid-feedback inline-feedback ml-2" v-show="errors.includes('transformer')">
        Please specify a transformer or remove the transformer
      </div>
    </div>

    <div v-if="template.items.length > 0" class="col-auto pr-0 form-inline">
      <template v-for="item in template.items">
        <div v-if="item.type === 'boolean'" class="form-check">
          <input class="form-check-input" type="checkbox" :id="`tr_${item.key}_${id}`"
                 v-model="transformer.parameters[item.key]"
                 v-bind:class="{'is-invalid': errors.includes(`transformer_value_${item.key}`)}">

          <label class="form-check-label small" :for="`tr_${item.key}_${id}`">
            {{ item.label }}
          </label>
        </div>

        <template v-else-if="item.type === 'choices'">
          <label v-if="item.label" class="small mr-2" :for="`tr_${item.key}_${id}`">
            {{ item.label }}
          </label>

          <select :id="`tr_${item.key}_${id}`" class="form-control form-control-sm mr-2 h-auto"
                  v-model="transformer.parameters[item.key]"
                  v-bind:class="{'is-invalid': errors.includes(`transformer_value_${item.key}`)}">
            <option disabled selected value="">Select an option</option>
            <option v-for="(choiceLabel, choiceValue) in item.choices" :value="choiceValue">
              {{ choiceLabel }}
            </option>
          </select>
        </template>

        <b-form-tags v-else-if="item.type === 'tags'"
                     :id="`tr_${item.key}_${id}`" separator=" " :placeholder="item.label || 'Specify tags'"
                     v-model="transformer.parameters[item.key]" size="sm" class="tags-size" remove-on-delete
                     v-bind:class="{'is-invalid': errors.includes(`transformer_value_${item.key}`)}"/>

        <template v-else>
          <label v-if="item.label" class="small mr-2" :for="`tr_${item.key}_${id}`">
            {{ item.label }}
          </label>

          <input class="form-control form-control-sm mr-2" :id="`tr_${item.key}_${id}`"
                 v-model="transformer.parameters[item.key]"
                 v-bind:class="{'w-text': item.size !== 'small' && item.size !== 'large',
                                  'w-small-text': item.size === 'small', 'w-large-text':  item.size === 'large',
                                  'is-invalid': errors.includes(`transformer_value_${item.key}`)}">
        </template>

        <div class="invalid-feedback inline-feedback mr-2"
             v-show="errors.includes(`transformer_value_${item.key}`)">
          Please specify a valid value
        </div>
      </template>
    </div>

    <div class="col-auto p-0 pb-1 ml-2">
      <button-delete @click="$emit('remove')" size="sm" class="btn-sm"/>
    </div>
  </div>
</template>

<script>
    import props from "@/utils/props";
    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "Transformer",
        mixins: [ValidationMixin],
        data() {
            return {
                availableTransformers: props.transformers,
            };
        },
        props: ['id', 'transformer'],
        computed: {
            template() {
                if (this.availableTransformers.hasOwnProperty(this.transformer.name))
                    return this.availableTransformers[this.transformer.name];

                return {label: '', items: []};
            },
        },
        methods: {
            validateTransformer() {
                if (!this.validateField('transformer',
                    this.transformer.name && this.transformer.name.length > 0))
                    return false;

                let transformerValid = true;
                this.template.items.forEach(transformerItem => {
                    const field = `transformer_value_${transformerItem.key}`;
                    const value = this.transformer.parameters[transformerItem.key];

                    let isValid = true;
                    switch (transformerItem.type) {
                        case 'string':
                        case 'choices':
                        case 'tags':
                            isValid = transformerItem.allowEmptyValue || (value && value.length > 0);
                            break;
                    }

                    if (!this.validateField(field, isValid))
                        transformerValid = false;
                });

                return transformerValid;
            },

            handleTransformerIndexChange() {
                this.transformer.parameters = {};
                this.template.items.forEach(valueItem => {
                    this.transformer.parameters[valueItem.key] = valueItem.defaultValue;
                });
            },
        },
    };
</script>