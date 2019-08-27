<template>
  <div class="border p-3" v-bind:class="[{'mt-2': !isFirst}, ...bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto">
        <div class="btn btn-sm bg-info-light border border-info text-info read-only m-1">
          <span class="font-weight-bold">Strength</span><br>
          {{ strength }}
        </div>
      </div>

      <div class="col">
        <div class="row flex-nowrap">
          <div class="col">
            <div class="row align-items-center m-0">
              <div class="property-path btn-sm read-only">
                Source
              </div>

              <div class="property-value property-value-scroll-parent btn-sm read-only ml-2">
                <div class="property-value-scroll">
                  {{ source }}
                </div>
              </div>
            </div>

            <properties :properties="sourceProperties" :show-resource-info="false"/>
          </div>

          <div class="col">
            <div class="row align-items-center m-0">
              <div class="property-path btn-sm read-only">
                Target
              </div>

              <div class="property-value property-value-scroll-parent btn-sm read-only ml-2">
                <div class="property-value-scroll">
                  {{ target }}
                </div>
              </div>
            </div>

            <properties :properties="targetProperties" :show-resource-info="false"/>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" @click="$emit('declined')">
              <fa-icon icon="times"/>
              Decline
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import Properties from "../../helpers/Properties";

    export default {
        name: "MatchLink",
        components: {
            Properties
        },
        props: {
            state: String,
            source: String,
            sourceValues: Array,
            target: String,
            targetValues: Array,
            strength: String,
            isFirst: Boolean,
        },
        computed: {
            bgColor() {
                if (this.state === 'accepted')
                    return 'bg-success';

                if (this.state === 'declined')
                    return 'bg-danger';

                return 'bg-white';
            },

            sourceProperties() {
                return this.sourceValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },

            targetProperties() {
                return this.targetValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },
        },
    };
</script>
