<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between">
      <div class="col-auto ml-4">
        <v-select :value="selected" label="label"
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

<!--      <div v-if="selectedSpec" class="col-auto">-->
<!--        <div class="btn-group-toggle" data-toggle="buttons">-->
<!--          <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showInfo}">-->
<!--            <input type="checkbox" autocomplete="off" v-model="showInfo"/>-->
<!--            <fa-icon icon="info-circle"/>-->
<!--            Show {{ this.element.type }} specs-->
<!--          </label>-->
<!--        </div>-->
<!--      </div>-->

      <div class="col-auto ml-auto">
        <div class="row">
          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Linkset/Lens and Create Group"/>
          </div>
        </div>
      </div>
    </div>

<!--    <div v-if="selectedSpec && showInfo" class="row">-->
<!--      <spec-info :type="this.element.type" :spec="selectedSpec"/>-->
<!--    </div>-->
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
        props: ['element', 'index', 'disabled'],
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
                    return {type: this.element.type, id: this.element.id, label: this.selectedSpec.label};

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