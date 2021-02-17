<template>
  <div class="border shadow p-2">
    <div class="row align-items-baseline justify-content-between">
      <div class="col-auto">
        <p class="font-italic smaller border rounded bg-opacity pointer m-0 px-2"
           v-bind:class="borderStyleClass" @click="visible = !visible">
          <fa-icon icon="chevron-down" size="xs" :class="visible ? null : 'collapsed'"></fa-icon>
          Open / close
        </p>
      </div>

      <div v-if="overrideFuzzyLogic" class="col-auto">
        <label class="font-weight-bold smaller m-0">
          Override t-conorm:

          <select class="font-italic smaller border rounded bg-opacity pl-1 ml-1"
                  v-bind:class="borderStyleClass">
            <option value="" selected>Do not override</option>
            <option v-for="(label, value) in tConorms" :value="value">{{ label }}</option>
          </select>
        </label>
      </div>
    </div>

    <b-collapse v-model="visible" class="mt-1">
      <div v-for="source in condition.sources" class="row align-items-center m-0">
        <div class="col-auto p-0">
          <property :entity-type-selection="$root.getEntityTypeSelectionById(source.entity_type_selection)"
                    :property="source.property" :read-only="true" :small="true"/>
        </div>

        <div class="col-auto font-weight-bold" v-if="source.transformers && source.transformers.length > 0">
          with transformer
          <span v-html="transformersHumanReadable(source)"/>
        </div>
      </div>

      <p class="font-weight-bold m-0">against</p>

      <div v-for="target in condition.targets" class="row align-items-center m-0">
        <div class="col-auto p-0">
          <property :entity-type-selection="$root.getEntityTypeSelectionById(target.entity_type_selection)"
                    :property="target.property" :read-only="true" :small="true"/>
        </div>

        <div class="col-auto font-weight-bold" v-if="target.transformers && target.transformers.length > 0">
          with transformer
          <span v-html="transformersHumanReadable(target)"/>
        </div>
      </div>

      <p class="font-weight-bold m-0">
        using

        <span class="text-secondary">{{ methodValueTemplate.label }}</span>

        <template v-if="methodValueTemplate.items.length > 0">
          [ <span v-html="methodValuePropsHumanReadable"/> ]
        </template>
      </p>
    </b-collapse>
  </div>
</template>

<script>
    import props from "../../utils/props";

    export default {
        name: "LinksetSpecConditionInfo",
        data() {
            return {
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
                tConorms: props.tConorms,
                visible: true,
            };
        },
        props: {
            condition: Object,
            overrideFuzzyLogic: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            borderStyleClass() {
                if (this.$parent.styleClass.includes('bg-primary-light'))
                    return 'border-primary';

                return 'border-secondary';
            },

            methodValueTemplate() {
                if (this.matchingMethods.hasOwnProperty(this.condition.method_name))
                    return this.matchingMethods[this.condition.method_name];

                return {label: '', items: []};
            },

            methodValuePropsHumanReadable() {
                return this.methodValueTemplate.items
                    .map(item => {
                        let value = this.condition.method_config[item.key];

                        if (item.choices)
                            value = Object.keys(item.choices).find(key => item.choices[key] === value);

                        if (item.label)
                            return `<span class="text-secondary">${item.label} = ${value}</span>`;

                        return `<span class="text-secondary">${value}</span>`;
                    })
                    .join(' and ');
            },
        },
        methods: {
            transformersHumanReadable(entityTypeSelection) {
                return entityTypeSelection.transformers
                    .map(transformer => {
                        const info = this.transformers[transformer.name];
                        const params = info.items
                            .map(item =>
                                `<span class="text-secondary">${item.label} = ${transformer.parameters[item.key]}</span>`)
                            .join(' and ');

                        if (!info.items || info.items.length === 0)
                            return `<span class="text-secondary">${info.label}</span>`;

                        return `<span class="text-secondary">${info.label}</span> [ ${params} ]`;
                    })
                    .join(' and ');
            },
        },
    }
</script>