<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between">
      <div class="col-auto ml-4">
        <v-select :value="selected" label="label" :options="specs" :clearable="false" :disabled="disabled"
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

      <div v-if="type === 'DIFFERENCE' || type.startsWith('IN_SET')"
           class="col-auto small text-muted font-italic">
        <template v-if="index === 0">Target</template>
        <template v-else>Filter</template>
      </div>

      <div v-if="selected" class="col-auto small text-muted font-italic">
        <template v-if="element.type === 'linkset'">Linkset</template>
        <template v-else>Lens</template>

        #{{ element.id }}
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
    import SpecInfo from "../../spec/SpecInfo";

    export default {
        name: "LensElement",
        components: {
            SpecInfo
        },
        mixins: [ValidationMixin],
        props: ['type', 'element', 'index', 'disabled'],
        data() {
            return {
                showInfo: false,
            };
        },
        computed: {
            selectedSpec() {
                return (this.element.type === 'linkset')
                    ? this.$root.getLinksetSpecById(this.element.id)
                    : this.$root.getLensSpecById(this.element.id);
            },

            selected() {
                if (this.selectedSpec)
                    return {type: this.element.type, specId: this.element.id, label: this.selectedSpec.label};

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
                        return lens.spec_id === lensSpec.id && lens.status === 'done' && lens.distinct_links_count > 0;
                    });
                });

                const specs = [
                    ...linksetSpecs.map(linksetSpec => ({
                        type: 'linkset',
                        specId: linksetSpec.id,
                        label: linksetSpec.label
                    })),
                    ...lensSpecs.map(lensSpec => ({
                        type: 'lens',
                        specId: lensSpec.id,
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
                this.element.id = selectedSpec.specId;

                this.$emit('update');
            },
        },
    };
</script>