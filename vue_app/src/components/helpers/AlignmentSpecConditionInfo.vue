<template>
  <div class="border shadow p-2">
    <div v-for="resource in condition.sources" class="row align-items-center">
      <div class="col-auto">
        <property :resource="$root.getResourceById(resource.resource)"
                  :property="resource.property" :read-only="true" :small="true"/>
      </div>

      <div class="col-auto font-weight-bold p-0" v-if="resource.transformers && resource.transformers.length > 0">
        with transformer
        <span v-html="resourceTransformersHumanReadable(resource)"/>
      </div>
    </div>

    <p class="font-weight-bold m-0">against</p>

    <div v-for="resource in condition.targets" class="row align-items-center">
      <div class="col-auto">
        <property :resource="$root.getResourceById(resource.resource)"
                  :property="resource.property" :read-only="true" :small="true"/>
      </div>

      <div class="col-auto font-weight-bold p-0" v-if="resource.transformers && resource.transformers.length > 0">
        with transformer
        <span v-html="resourceTransformersHumanReadable(resource)"/>
      </div>
    </div>

    <p class="font-weight-bold m-0">
      using

      <span class="text-info">{{ methodValueTemplate.label }}</span>

      <template v-if="methodValueTemplate.items.length > 0">
        [ <span v-html="methodValuePropsHumanReadable"/> ]
      </template>
    </p>
  </div>
</template>

<script>
    import props from "../../utils/props";

    export default {
        name: "AlignmentSpecConditionInfo",
        data() {
            return {
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
            };
        },
        props: {
            'condition': Object,
        },
        computed: {
            methodValueTemplate() {
                if (this.matchingMethods.hasOwnProperty(this.condition.method_name))
                    return this.matchingMethods[this.condition.method_name];

                return {label: '', items: []};
            },

            methodValuePropsHumanReadable() {
                return this.methodValueTemplate.items
                    .map(item => {
                        let value = this.condition.method_value[item.key];

                        if (item.choices)
                            value = Object.keys(item.choices).find(key => item.choices[key] === value);

                        if (item.label)
                            return `<span class="text-info">${item.label} = ${value}</span>`;

                        return `<span class="text-info">${value}</span>`;
                    })
                    .join(' and ');
            },
        },
        methods: {
            resourceTransformersHumanReadable(resource) {
                return resource.transformers
                    .map(transformer => {
                        const info = this.transformers[transformer.name];
                        const params = info.items
                            .map(item =>
                                `<span class="text-info">${item.label} = ${transformer.parameters[item.key]}</span>`)
                            .join(' and ');

                        if (!info.items || info.items.length === 0)
                            return `<span class="text-info">${info.label}</span>`;

                        return `<span class="text-info">${info.label}</span> [ ${params} ]`;
                    })
                    .join(' and ');
            },
        },
    }
</script>