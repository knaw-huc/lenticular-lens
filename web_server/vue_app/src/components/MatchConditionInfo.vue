<template>
  <div class="border shadow p-2">
    <template v-for="collection_properties in condition.sources">
      <div v-for="resource in collection_properties" class="row m-0">
        <property :property="resource.property" :read-only="true" :small="true"/>

        <p class="font-weight-bold m-0" v-if="resource.transformers">
          with transformers {{ resource.transformers.join(', ') }}
        </p>
      </div>
    </template>

    <p class="font-weight-bold m-0">against</p>

    <template v-for="collection_properties in condition.targets">
      <div v-for="resource in collection_properties" class="row m-0">
        <property :property="resource.property" :read-only="true" :small="true"/>

        <p class="font-weight-bold m-0" v-if="resource.transformers">
          with transformers
          <span class="text-info">{{ resource.transformers.join(', ') }}</span>
        </p>
      </div>
    </template>

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
    import props from "../utils/props";

    export default {
        name: "MatchConditionInfo",
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

                        if (this.condition.method_name === 'IS_IN_SET')
                            value = this.$root.matches.find(match => match.id === value.value).label;
                        else if (item.choices)
                            value = Object.keys(item.choices).find(key => item.choices[key] === value);

                        if (item.label)
                            return `<span class="text-info">${item.label} = ${value}</span>`;

                        return `<span class="text-info">${value}</span>`;
                    })
                    .join(' and ');
            }
        },
    }
</script>