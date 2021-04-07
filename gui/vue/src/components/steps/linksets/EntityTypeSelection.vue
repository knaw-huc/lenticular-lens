<template>
  <div class="row align-items-center">
    <div v-if="!entityTypeSelection" class="col-auto pr-0">
      <select-box :id="'linkset_' + linksetSpec.id + '_entity_type_selection_label_' + id" :value="entityTypeSelection"
                  v-bind:class="{'is-invalid': errors.includes('entityTypeSelection')}"
                  @input="$emit('input', parseInt($event))">
        <option disabled selected value="">Choose an entity-type selection</option>
        <option v-for="ets in entityTypeSelections" :value.number="ets.id">
          {{ ets.label }}
        </option>
      </select-box>

      <div class="invalid-feedback" v-show="errors.includes('entityTypeSelection')">
        Please select an entity-type selection
      </div>
    </div>

    <div v-else class="ml-3">
      {{ entityTypeSelection.label }}
    </div>

    <div class="col-auto pl-0 ml-3">
      <button-delete size="sm" class="btn-sm" @click="$emit('remove')"/>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "EntityTypeSelection",
        mixins: [ValidationMixin],
        props: {
            linksetSpec: Object,
            entityTypeSelection: Object,
            id: String,
            selectionKey: String,
        },
        computed: {
            entityTypeSelections() {
                return this.$root.entityTypeSelections.filter(entityTypeSelection => {
                    return !this.linksetSpec[this.selectionKey].includes(entityTypeSelection.id.toString());
                });
            },
        },
        methods: {
            validateEntityTypeSelection() {
                return this.validateField('entityTypeSelection',
                    this.entityTypeSelection && this.entityTypeSelection !== '');
            },
        },
    };
</script>