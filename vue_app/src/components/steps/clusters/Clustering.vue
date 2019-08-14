<template>
  <sub-card :small-spacing="true" :is-first="isFirst" v-bind:class="selected ? 'bg-info-light' : {}">
    <div @click="$emit('select:clusterId', clusterId)">
      <div class="row">
        <div class="col font-weight-bold">
          {{ clusterId }}
        </div>

        <div class="col" v-bind:class="'ext_' + clusterData.extended">
          {{ clusterData.extended }}
        </div>

        <div class="col" v-bind:class="'ext_' + clusterData.reconciled">
          {{ clusterData.reconciled }}
        </div>

        <div class="col">
          {{ clusterData.nodes.length }}
        </div>

        <div class="col">
          {{ clusterData.links.length }}
        </div>

        <div class="col-4">
          <properties :properties="props"/>
        </div>
      </div>
    </div>
  </sub-card>
</template>

<script>
    import SubCard from '../../structural/SubCard';
    import Properties from "../../helpers/Properties";

    export default {
        name: "Clustering",
        components: {
            SubCard,
            Properties,
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
                const props = Object.entries(this.properties)
                    .filter(([resourceId, _]) => this.resources.includes(resourceId))
                    .flatMap(([_, value]) => value)
                    .reduce((acc, value) => {
                        const property = [this.$root.getResourceByDatasetId(value.dataset).id, value.property];
                        let propAndValues =
                            acc.find(pv => pv.property[0] === property[0] && pv.property[1] === property[1]);

                        if (!propAndValues) {
                            propAndValues = {property, values: []};
                            acc.push(propAndValues);
                        }

                        propAndValues.values.push(...value.values);

                        return acc;
                    }, []);

                props.forEach(pv => pv.values = [...new Set(pv.values)]);
                return props;
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