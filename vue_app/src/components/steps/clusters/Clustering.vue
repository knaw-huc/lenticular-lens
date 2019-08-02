<template>
  <sub-card :small-spacing="true" :is-first="isFirst" v-bind:class="selected ? 'bg-info-light' : {}">
    <div @click="$emit('select:clusterId', clusterId)">
      <div class="row">
        <div class="col font-weight-bold" v-bind:class="'ext_' + clusterData.extended">
          {{ clusterData.extended }}
        </div>

        <div class="col font-weight-bold" v-bind:class="'ext_' + clusterData.reconciled">
          {{ clusterData.reconciled }}
        </div>

        <div class="col">
          {{ clusterId }}
        </div>

        <div class="col">
          {{ clusterData.index }}
        </div>

        <div class="col">
          {{ clusterData.nodes.length }}
        </div>
      </div>

      <div class="row">
        <div class="col">
          <property
              v-for="(prop, idx) in props"
              :key="idx"
              :property="prop.property"
              :values="prop.values"
              :read-only="true"/>
        </div>
      </div>
    </div>
  </sub-card>
</template>

<script>
    import SubCard from '../../structural/SubCard';

    export default {
        name: "Clustering",
        components: {
            SubCard
        },
        props: {
            clusterId: String,
            clusterData: Object,
            properties: Object,
            selected: false,
            isFirst: false,
        },
        computed: {
            resources() {
                const linkResources = this.clusterData.links
                    .flatMap(links => links)
                    .map(res => res.substring(1, res.length - 1));

                const nodeResources = this.clusterData.nodes
                    .map(res => res.substring(1, res.length - 1));

                return [...new Set(linkResources.concat(nodeResources))];
            },

            props() {
                return Object.entries(this.properties)
                    .filter(([resourceId, _]) => this.resources.includes(resourceId))
                    .slice(0, 5)
                    .flatMap(([_, value]) => value)
                    .map(value => {
                        return {
                            property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                            values: value.values,
                        };
                    });
            },
        },
    }
</script>

<style>
  .ext_cyc {
    color: purple;
  }

  .ext_yes {
    color: blue;
  }

  .ext_no {
    color: red;
  }
</style>