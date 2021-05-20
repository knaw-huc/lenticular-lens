<template>
  <div class="border p-3 mb-4 link-scroll" v-bind:class="[bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <span class="font-weight-bold">
            <span v-if="isActive" class="mr-1">&#8680;</span>
            <span class="font-italic"># {{ index + 1 }}</span>
          </span>
        </div>

        <div class="col-auto">
          <div class="info-block">
            <span class="font-weight-bold">Similarity</span><br>
            {{ similarity }}
          </div>
        </div>

        <div v-if="link.cluster_id" class="col-auto">
          <div class="info-block">
            <span class="font-weight-bold">Cluster</span><br>
            <span class="font-italic"># {{ link.cluster_id }}</span>
          </div>
        </div>
      </div>

      <div class="col">
        <div class="text-break-all">
          <span class="font-weight-bold">Source URI:</span>

          <span class="text-secondary">
            {{ switchSourceAndTarget ? link.target : link.source }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copySourceUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div class="text-break-all">
          <span class="font-weight-bold">Target URI:</span>

          <span class="text-secondary">
            {{ switchSourceAndTarget ? link.source : link.target }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copyTargetUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div v-if="sourceValues.length > 0 || targetValues.length > 0" class="row flex-nowrap border-top mt-2 pt-2">
          <div class="col">
            <div class="font-weight-bold mb-2">Source properties:</div>
            <property-values v-for="(prop, idx) in (switchSourceAndTarget ? targetValues : sourceValues)"
                             :key="idx" v-if="prop.values && prop.values.length > 0"
                             :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                             :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
          </div>

          <div class="col">
            <div class="font-weight-bold mb-2">Target properties:</div>
            <property-values v-for="(prop, idx) in (switchSourceAndTarget ? sourceValues : targetValues)"
                             :key="idx" v-if="prop.values && prop.values.length > 0"
                             :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                             :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" :disabled="isUpdating" title="Accept (a)"
                    @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" :disabled="isUpdating" title="Reject (x)"
                    @click="$emit('rejected')">
              <fa-icon icon="times"/>
              Reject
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-warning m-1" :disabled="isUpdating" title="Not sure (space)"
                    @click="$emit('not_sure')">
              <fa-icon icon="question"/>
              Not sure
            </button>
          </div>

          <div class="col-auto mt-2">
            <b-dropdown size="sm" variant="outline-dark" class="m-1" :disabled="isUpdating" title="Add motivation (m)"
                        @show="onOpenMotivation" @hide="onCloseMotivation" @shown="focusOnMotivationTextarea"
                        ref="motivationBtn">
              <template #button-content>
                <fa-icon icon="pencil-alt"/>
                {{ link.motivation ? 'Update' : 'Add' }} motivation
              </template>

              <b-dropdown-form>
                <div class="form-group mb-2">
                  <textarea class="form-control motivation" v-model="motivation"></textarea>
                </div>

                <div class="text-right">
                  <button type="button" class="btn btn-sm border mr-3" :disabled="isUpdating" title="Close (Esc)"
                          @click="closeMotivationButton(false)">
                    Close
                  </button>

                  <button type="button" class="btn btn-sm border" :disabled="isUpdating" title="Save (Shift + Enter)"
                          @click="closeMotivationButton(true)">
                    Save
                  </button>
                </div>
              </b-dropdown-form>
            </b-dropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import PropertyValues from "../../helpers/PropertyValues";

    export default {
        name: "Link",
        components: {
            PropertyValues
        },
        data() {
            return {
                motivation: '',
                motivationIsOpen: false,
            };
        },
        props: {
            index: Number,
            link: Object,
            isActive: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            similarity() {
                return this.link.similarity && !isNaN(this.link.similarity)
                    ? this.link.similarity.toFixed(3) : '1.000';
            },

            switchSourceAndTarget() {
                return this.link.link_order === 'target_source';
            },

            sourceValues() {
                return this.link.source_values || [];
            },

            targetValues() {
                return this.link.target_values || [];
            },

            isUpdating() {
                return this.link.updating;
            },

            bgColor() {
                switch (this.link.valid) {
                    case 'accepted':
                        return 'bg-success';
                    case 'rejected':
                        return 'bg-danger';
                    case 'not_sure':
                        return 'bg-warning';
                    case 'mixed':
                        return 'bg-warning';
                    default:
                        return 'bg-white';
                }
            },
        },
        methods: {
            openMotivationButton() {
                if (!this.motivationIsOpen)
                    this.$refs.motivationBtn.visible = true;
            },

            closeMotivationButton(save = false) {
                if (this.motivationIsOpen) {
                    this.$refs.motivationBtn.visible = false;
                    if (save)
                        this.$emit('motivation', this.motivation);
                }
            },

            onOpenMotivation() {
                this.motivationIsOpen = true;
                this.motivation = this.link.motivation;
                this.$emit('motivation_open');
            },

            onCloseMotivation() {
                this.motivationIsOpen = false;
                this.$emit('motivation_close');
            },

            focusOnMotivationTextarea() {
                this.$refs.motivationBtn.$el.querySelector('textarea').focus();
            },

            async copySourceUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.target : this.link.source);
            },

            async copyTargetUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.source : this.link.target);
            },
        },
    };
</script>
