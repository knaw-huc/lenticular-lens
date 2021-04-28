<template>
  <b-modal ref="filterConfig" body-class="bg-light" size="xl" hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Filter configuration</h5>

      <button class="btn btn-secondary btn-sm ml-auto" @click="saveProperties">
        Save
      </button>

      <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
    </template>

    <resource-filter v-for="(filter, idx) in filters" :key="idx" :id="idx" :filter="filter"
                     :is-first="idx === 0" ref="resourceFilters"/>
  </b-modal>
</template>

<script>
    import LogicBox from "@/components/helpers/LogicBox";
    import FilterCondition from "@/components/helpers/FilterCondition";

    import ValidationMixin from "@/mixins/ValidationMixin";

    import ResourceFilter from './ResourceFilter';

    export default {
        name: "FilterConfig",
        components: {
            LogicBox,
            FilterCondition,
            ResourceFilter,
        },
        props: {
            filters: Array,
        },
        methods: {
            show() {
                this.$refs.filterConfig.show();
            },

            async saveProperties() {
                if (this.$refs.resourceFilters)
                    this.$refs.resourceFilters.forEach(resourceFilter => resourceFilter.validateResourceFilter());

                await this.$root.submit();
                this.$emit('save');
            },
        },
    };
</script>
