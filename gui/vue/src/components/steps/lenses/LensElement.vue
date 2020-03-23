<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between">
      <div class="col-auto mr-auto ml-4">
        <select-box v-model.number="element.alignment" v-bind:class="{'is-invalid': errors.includes('alignment')}"
                    @change="$emit('alignment')">
          <option disabled selected value="">Select an alignment</option>
          <option v-for="alignment in alignments" :value="alignment.id">{{ alignment.label }}</option>
        </select-box>

        <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('alignment')}">
          Please specify an alignment
        </div>
      </div>

      <div class="col-auto ml-auto">
        <div class="row">
          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Alignment and Create Group"/>
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
            alignments() {
                return this.$root.matches.filter(match => {
                    return this.$root.alignments.find(al => {
                        return al.alignment === match.id && al.status === 'done' && al.distinct_links_count > 0;
                    });
                });
            },
        },
        methods: {
            validateLensElement() {
                return this.validateField('alignment', this.element.alignment !== null);
            }
        },
    };
</script>