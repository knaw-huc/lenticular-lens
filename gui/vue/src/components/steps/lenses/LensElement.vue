<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between">
      <div class="col-auto mr-auto ml-4">
        <v-select :value="selectedSpec" label="label"
                  :options="specs" :clearable="false" :disabled="disabled"
                  autocomplete="off" placeholder="Type to search for a linkset or lens"
                  @input="updateLensElement" v-bind:class="{'is-invalid': errors.includes('spec')}">
          <div slot="option" slot-scope="option">
            <span class="pr-2">{{ option.label }}</span>
            <span class="font-italic text-muted small">{{ option.type }}</span>
          </div>
        </v-select>

        <div class="invalid-feedback" v-show="errors.includes('spec')">
          Please select a linkset or lens
        </div>
      </div>

      <div class="col-auto ml-auto">
        <div class="row">
          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Linkset/Lens and Create Group"/>
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
        props: ['element', 'index', 'disabled'],
        computed: {
            selectedSpec() {
                const spec = (this.element.type === 'linkset')
                    ? this.$root.getLinksetSpecById(this.element.id)
                    : this.$root.getLensSpecById(this.element.id);

                if (spec)
                    return {type: this.element.type, id: this.element.id, label: spec.label};

                return null;
            },

            specs() {
                const linksetSpecs = this.$root.linksetSpecs.filter(linksetSpec => {
                    return this.$root.linksets.find(linkset => {
                        return linkset.spec_id === linksetSpec.id
                            && linkset.status === 'done' && linkset.distinct_links_count > 0;
                    });
                });

                const lensSpecs = this.$root.lensSpecs.filter(lensSpec => {
                    return this.$root.lenses.find(lens => {
                        return lens.spec_id === lensSpec.id && lens.status === 'done' && lens.links_count > 0;
                    });
                });

                const specs = [
                    ...linksetSpecs.map(linksetSpec => ({
                        type: 'linkset',
                        id: linksetSpec.id,
                        label: linksetSpec.label
                    })),
                    ...lensSpecs.map(lensSpec => ({
                        type: 'lens',
                        id: lensSpec.id,
                        label: lensSpec.label
                    }))
                ];

                specs.sort((specA, specB) => specA.label.localeCompare(specB.label));

                return specs;
            },
        },
        methods: {
            validateLensElement() {
                return this.validateField('id', this.element.id !== null);
            },

            updateLensElement(selectedSpec) {
                this.element.type = selectedSpec.type;
                this.element.id = selectedSpec.id;

                this.$emit('update');
            },
        },
    };
</script>