<template>
  <div class="border p-3 mb-2"
       v-bind:class="[{'clickable': selectable}, selected ? 'bg-info-light' : 'bg-primary-light']"
       @click="selectable && $emit('select:clusterId', cluster.id)">
    <div class="row">
      <div class="col">
        <div>
          <strong>{{ cluster.id }}</strong>
        </div>

        <div>
          <strong>Size: </strong>
          {{ cluster.size.toLocaleString('en') }}

          <span class="px-4">&bull;</span>

          <strong>Links: </strong>
          {{ cluster.links.toLocaleString('en') }}
        </div>

        <div>
          <strong>Extended: </strong>
          <span v-bind:class="'ext_' + cluster.extended">{{ cluster.extended }} </span>

          <span class="px-4">&bull;</span>

          <strong>Reconciled: </strong>
          <span v-bind:class="'ext_' + cluster.reconciled">{{ cluster.reconciled }} </span>
        </div>
      </div>

      <div class="col-8">
        <properties :properties="props" :show-resource-info="false"/>
      </div>
    </div>
  </div>
</template>

<script>
    import Properties from "../../helpers/Properties";

    export default {
        name: "Cluster",
        components: {
            Properties,
        },
        props: {
            index: Number,
            cluster: Object,
            selected: false,
            selectable: {
                type: Boolean,
                default: true
            }
        },
        computed: {
            props() {
                return this.cluster.values.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },
        },
    };
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