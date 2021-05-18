<template>
  <sub-card :has-columns="true" :has-error="errors.includes('filters')" :is-first="isFirst">
    <template v-slot:columns>
      <div class="col-auto pr-0">
        <div class="property">
          <span class="first-el"/>

          <div class="property-pill property-resource read-only" :title="dataset.uri">
            {{ dataset.title }}
          </div>

          <div class="property-pill property-resource read-only" :title="collection.uri">
            {{ collection.title || collection.shortenedUri || collectionId }}
          </div>
        </div>
      </div>
    </template>

    <logic-box :element="filter.filter" elements-name="conditions" :is-root="true"
               :group="'view_filter_' + id" :uid="'view_filter_' + id + '_filter_group_0'"
               validate-method-name="validateFilterCondition" empty-elements-text="No conditions"
               validation-failed-text="Please provide at least one condition" v-slot="curCondition"
               @add="addFilterCondition($event)" ref="filterGroup">
      <filter-condition
          :graphql-endpoint="filter.timbuctoo_graphql"
          :dataset-id="filter.dataset_id"
          :collection-id="filter.collection_id"
          :condition="curCondition.element"
          :index="curCondition.index"
          @add="curCondition.add()"
          @remove="curCondition.remove()"/>
    </logic-box>
  </sub-card>
</template>

<script>
    import LogicBox from "@/components/helpers/LogicBox";
    import FilterCondition from "@/components/helpers/FilterCondition";

    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "ResourceFilter",
        mixins: [ValidationMixin],
        components: {
            LogicBox,
            FilterCondition,
        },
        props: {
            id: Number,
            filter: Object,
            isFirst: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            dataset() {
                const datasets = this.$root.getDatasets(this.filter.timbuctoo_graphql);
                return datasets[this.filter.dataset_id];
            },

            collection() {
                return this.dataset.collections[this.filter.collection_id];
            },
        },
        methods: {
            validateResourceFilter() {
                return this.validateField('filters', this.$refs.filterGroup.validateLogicBox());
            },

            addFilterCondition(group) {
                group.conditions.push({
                    type: '',
                    property: [''],
                });
            },
        },
    };
</script>
