<template>
  <div class="bg-white border p-3" v-bind:class="{'mt-2': !isFirst}">
    <div class="row align-items-center">
      <div class="col-auto">
        <div class="btn btn-sm bg-info-light border border-info text-info m-1">
          <span class="font-weight-bold">Strength</span><br>
          {{ strength }}
        </div>
      </div>

      <div class="col">
        <properties :properties="sourceProperties"/>
      </div>

      <div class="col">
        <properties :properties="targetProperties"/>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1">
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
            source: String,
            sourceValues: Array,
            target: String,
            targetValues: Array,
            strength: String,
            isFirst: Boolean
        },
        computed: {
            sourceProperties() {
                const sourceProperties = this.sourceValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    }
                });

                if (sourceProperties.length > 0)
                    sourceProperties.unshift({
                        property: [sourceProperties[0].property[0], 'uri'],
                        values: [this.source],
                    });

                return sourceProperties;
            },

            targetProperties() {
                const targetProperties = this.targetValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    }
                });

                if (targetProperties.length > 0)
                    targetProperties.unshift({
                        property: [targetProperties[0].property[0], 'uri'],
                        values: [this.target],
                    });

                return targetProperties;
            },
        },
    }
</script>
