<template>
  <div class="border p-3 mb-2"
       v-bind:class="[{'clickable': selectable}, selected ? 'bg-info-light' : 'bg-primary-very-light']"
       @click="selectable && $emit('select:clusterId', cluster.id)">
    <div class="row">
      <div class="col">
        <div class="text-info">
          <strong>{{ cluster.id }}</strong>
        </div>

        <div class="row">
          <div class="col">
            <strong>Size: </strong>
            {{ cluster.size.toLocaleString('en') }}
          </div>

          <div class="col">
            <strong>Extended: </strong>
            <span v-bind:class="'ext_' + cluster.extended">{{ cluster.extended }}</span>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <strong>Links: </strong>
            {{ cluster.links.toLocaleString('en') }}
          </div>

          <div class="col">
            <strong>Reconciled: </strong>
            <span v-bind:class="'ext_' + cluster.reconciled">{{ cluster.reconciled }}</span>
          </div>
        </div>
      </div>

      <div class="col-8">
        <properties :properties="cluster.values"/>
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