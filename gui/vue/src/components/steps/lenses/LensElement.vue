<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between">
      <div class="col-auto mr-auto ml-4">
        <select-box v-model.number="element.id" v-bind:class="{'is-invalid': errors.includes('id')}"
                    @change="$emit('linkset')">
          <option disabled selected value="">Select a linkset</option>
          <option v-for="linksetSpec in linksetSpecs" :value="linksetSpec.id">{{ linksetSpec.label }}</option>
        </select-box>

        <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('id')}">
          Please specify a linkset
        </div>
      </div>

      <div class="col-auto ml-auto">
        <div class="row">
          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Linkset and Create Group"/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "LensElement",
        mixins: [ValidationMixin],
        props: ['element', 'index'],
        computed: {
            linksetSpecs() {
                return this.$root.linksetSpecs.filter(linksetSpec => {
                    return this.$root.linksets.find(al => {
                        return al.spec_id === linksetSpec.id && al.status === 'done' && al.distinct_links_count > 0;
                    });
                });
            },
        },
        methods: {
            validateLensElement() {
                return this.validateField('id', this.element.id !== null);
            }
        },
    };
</script>