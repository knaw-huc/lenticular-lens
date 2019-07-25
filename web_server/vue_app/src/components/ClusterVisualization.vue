<template>
  <div>
    <div class="border p-4 mt-4 bg-white">
      <div class="row align-items-center">
        <div class="col-auto">
          <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_1></octicon>
        </div>

        <div class="col" v-b-toggle.cluster_plot_row_1>
          <div class="row">
            <div class="col-auto h3 pr-0">Cluster</div>
            <div class="col-auto pl-0">
              <button-info popup_title="CLUSTER VISUALIZATION">
                <div class="text-left">
                  <div class="h2">Identity Link Network (ILN)</div>

                  <p class="h5 pt-4 pl-5">
                    This provides additional information of Identity Link Clusters:
                  </p>

                  <ul class="h5 ml-5">
                    <li>Identity Link Clusters.</li>
                    <li>Visualize a cluster and interact with it.</li>
                    <li>An improved visualisation (particularly important for large clusters).</li>
                    <li>Reconcile a cluster using additional information such relation.</li>
                  </ul>

                  <div class="h3 pt-4">An ILN of <strong>Meulder Hans</strong> in the Turtle Language</div>
                  <p class="h5 pt-4 pb-4 pl-5">
                    This is an example of links discovered using an approximate string similarity on
                    <strong>Ecartico</strong>, <strong>Baptism</strong>, <strong>Marriage</strong> and
                    <strong>Burial</strong> for married Amsterdammers between 1600 and 1650. These links are
                    specifically the ones that link different occurrences of <strong>Meulder Hans</strong>.
                  </p>

                  <textarea disabled cols="75" rows="18" class="ml-5 mb-1">
        @prefix baptism: <http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/> .
        @prefix ecartico: <http://www.vondel.humanities.uva.nl/ecartico/persons/> .
        @prefix marriage: <http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .

        baptism:saaId24678323p2 owl:sameAs ecartico:15747 .
        baptism:saaId24678323p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24519437p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24285260p2 owl:sameAs baptism:saaId24519437p2 .
        marriage:saaId26379331p1 owl:sameAs ecartico:15747 .
        baptism:saaId24519437p2 owl:sameAs ecartico:15747 .
        baptism:saaId24519437p2 owl:sameAs marriage:saaId26377774p1 .
        baptism:saaId24285260p2 owl:sameAs ecartico:15747 .
        baptism:saaId24285260p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24519437p2 owl:sameAs baptism:saaId24678323p2 .
        marriage:saaId26377774p1 owl:sameAs ecartico:15747 .
        marriage:saaId26377774p1 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24285260p2 owl:sameAs baptism:saaId24678323p2 .</textarea>

                  <div class="h3 pt-4">Visualizing an ILN of <strong>Meulder Hans</strong></div>

                  <p class="h5 pt-4 pl-5">
                    The cluster of <strong>Meulder Hans</strong> is composed of 6 nodes (potentially the same person)
                    using 13 link. The links in plain black represent an exact match (link strength = 1) while those in
                    dotted red represent a link of strength below 1. The color of the node depicts the data-source it is
                    stemmed from. So in this real example cluster,
                  </p>
                  <ul class="h5 ml-5">
                    <li>Three nodes are from <strong>Baptism</strong>;</li>
                    <li>Two nodes are from <strong>Marriage</strong> and;</li>
                    <li>One is from <strong>Ecartico</strong>.</li>
                  </ul>

                  <div class="text-center pt-4">
                    <img src="/static/images/1 Meulder Hans (Cluster).jpg" width="700" height="600"/>
                  </div>
                </div>
              </button-info>
            </div>
          </div>
        </div>

        <div class="col-auto" v-b-toggle.cluster_plot_row_1>
          <button type="button" v-if="association"
                  @click="getGraphData('cluster')" class="btn btn-info mr-4">
            Load Original Clusters
          </button>

          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </div>
      <b-collapse
          :visible="!Boolean(association)"
          id="cluster_plot_row_1"
          ref="vis_collapse_1"
      >
        <svg class="plot mt-3" id="graph_cluster_1"></svg>
      </b-collapse>
    </div>

    <div class="border p-4 mt-4 bg-white">
      <div class="row align-items-center">
        <div class="col-auto">
          <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_2></octicon>
        </div>

        <div class="col" v-b-toggle.cluster_plot_row_2>
          <div class="row">
            <div class="col-auto h3 pr-0">Compact Cluster</div>
            <div class="col-auto pl-0">
              <button-info popup_title="CLUSTER VISUALIZATION">
                <div class="text-left">
                  <div class="h3">A Compact Representation of Meulder Hans' ILN</div>
                  <p class="h5 pt-4 pl-5">
                    The compact representation of a cluster allows for the display of large clusters and a comprehensive
                    aggravation of nodes. The approach groups nodes base on similar link strength starting from the
                    highest strength in the identity network. From the original cluster, two sub-groups of nodes can be
                    identified using the link strength of 1 (black plain link) together.
                  </p>

                  <ul class="h5 ml-5">
                    <li>Sub-group-1: Two nodes are linked with strength 1</li>
                    <li>Sub-group-2: Three nodes are linked with strength 1</li>
                    <li>Sub-group-3: One isolated node</li>
                  </ul>

                  <p class="h5 pt-4 pl-5">
                    The subgroups are then interconnected using an aggregated link represented by the highest strength.
                    Using such approach sub-groups and their interconnections are now clearly visible.
                  </p>

                  <p class="h5 pt-4 pl-5">
                    Each compact node contains 3 type of information:
                  </p>

                  <ul class="h5 ml-5">
                    <li><strong>N</strong> indicating the number of nodes aggregated by the compact node.</li>
                    <li><strong>L</strong> indicating the number of links.</li>
                    <li><strong>S</strong> indicating the strength of the links that enabled the aggregation.</li>
                    <li>The last information (not present in this example but visible in the second compact example of
                      size 35) removes a percentage of the node's color to indicate the number of missing links for the
                      number of nodes aggregated
                    </li>
                  </ul>


                  <div class="text-center pt-4">
                    <img src="/static/images/1 Meulder Hans (Cluster).jpg" width="700"/>
                    <p class="h5 pt-4 pl-5 font-weight-bold">
                      Original Cluster
                    </p>
                  </div>

                  <div class="text-center pt-4">
                    <img src="/static/images/2 Meulder Hans (Cluster-Compact).jpg" width="700"/>
                    <p class="h5 pt-4 pl-5 font-weight-bold">
                      Compact Cluster
                    </p>
                  </div>

                  <div class="h3 pt-4">Large ILN Versus its Compact Version</div>

                  <p class="h5 pt-4 pl-5">
                    This is an example of a bigger cluster of size 35 potentially representing <strong>Pieterss
                    Grietje</strong>. The larger an ILN gets, the less comprehensive it is visually. Especially when it
                    highlight a mesh topology. For this very reason, the compact version of the visual ILN is of
                    importance for visual aid for validation purposes.
                  </p>

                  <div class="text-center pt-4">
                    <img src="/static/images/1  Pieters Grietje (Cluster).jpg" width="800"/>
                  </div>

                  <p class="h5 pt-4 pl-5">
                    This is the compact version of a cluster of size 35 potentially representing <strong>Pieterss
                    Grietje</strong>. In this examople, 35 nodes are now converted into 4 compact nodes of size 25, 3, 2
                    and two. The last two nodes are of size one. The compact node of size 25 is composed of 294 limks
                    insted of 300. Meaning 6 links are missing.
                  </p>

                  <div class="text-center pt-4">
                    <img src="/static/images/2  Pieters Grietje (Cluster-Compact).jpg" width="800"/>
                  </div>

                  <div class="h3 pt-5">Expanding a Compact Node with Double-Click</div>

                  <p class="h5 pt-4 pl-5">
                    For a better validation experience, each of the compact nodes can be expanded. This allows a
                    detailed understanding on the type of network (START - LINE - MESH) that defines the aggragated
                    node. When a compact node (sub-cluster) is double-clicked, for example the one of size 3, it is
                    highlighted in red as shown in on the left side the figure below, and its expanded version is
                    ploted, as shown in the right side of the figure.
                  </p>

                  <div class="text-center pt-4">
                    <img src="/static/images/3 Meulder Hans (Cluster-Compact Selected).jpg" width="1000"/>
                  </div>
                </div>
              </button-info>
            </div>
          </div>
        </div>

        <div class="col-auto" v-b-toggle.cluster_plot_row_2>
          <button type="button" v-if="association"
                  @click="getGraphData('cluster')" class="btn btn-info mr-4">
            Load Original Compact Clusters
          </button>

          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </div>
      <b-collapse
          :visible="!Boolean(association)"
          id="cluster_plot_row_2"
          ref="vis_collapse_1"
      >
        <svg class="plot mt-3" id="graph_cluster_2"></svg>
      </b-collapse>
    </div>

    <div v-if="association" class="border p-4 mt-4 bg-white">
      <div class="row align-items-center">
        <div class="col-auto">
          <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_3></octicon>
        </div>

        <div class="col" v-b-toggle.cluster_plot_row_3>
          <div class="row">
            <div class="col-auto h3 pr-0">Reconciled</div>
            <div class="col-auto pl-0">
              <button-info popup_title="RECONCILED CLUSTER VISUALIZATION">
                <div class="text-left">
                  <div class="h2">Reconciling an ILN</div>

                  <p class="h5 pt-4 pl-5">
                    We enable the reconciliation of an ILN using relations between discovered ILN. For the current
                    example, the relation used is the marital status meaning married people. In this example, the ILN to
                    reconcile is the one of <strong>Meulder Hans</strong>. It is the one in <strong>blue</strong> and it
                    connect to two other clusters using purple dotted lines. Reading the graph, the other two clusters
                    indicate that <strong>Meulder Hans</strong> appears to be connected to two women: **Petsinck
                    Catharina (orange)<strong> and </strong>Jans Fijtje (green)**.
                  </p>

                  <p class="h5 pt-4 pl-5">
                    We provide two representation where the first picture presents a compact representation of all
                    clusters while the second representation presents a non compact representation of the investigated
                    cluster: <strong>Meulder Hans</strong>.
                  </p>

                  <p class="h5 pt-4 pl-5">
                    Now, given this additional marital status, is it plausible that all nodes representing <strong>Meulder
                    Hans</strong> are indeed representing the same person?
                  </p>

                  <p class="h5 pt-4 pl-5">
                    To answer this questions, we make use of the existence of <strong>cycle</strong> to materialise
                    strong evidence.
                  </p>

                  <div class="text-center pt-4">
                    <img src="/static/images/4 Meulder Hans (Cluster-Compact Compact-Evidence).jpg" width="900"/>
                  </div>

                  <div class="text-center pt-4">
                    <img src="/static/images/5 Meulder Hans (Cluster-Compact Evidence).jpg" width="900"/>
                  </div>

                  <div class="h2 pt-4">Reconciled Nodes</div>
                </div>
              </button-info>
            </div>
          </div>
        </div>

        <div class="col-auto" v-b-toggle.cluster_plot_row_3>
          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </div>
      <b-collapse
          :visible="Boolean(association)"
          id="cluster_plot_row_3"
      >
        <svg class="plot mt-3" id="graph_cluster_3"></svg>
      </b-collapse>
    </div>

    <b-modal
        id="visualization_popup"
        ref="visualization_popup"
        title="CLUSTER DETAIL"
        size="xl"
        hide-footer
        :return-focus="$root.$children[0].$el"
        :static="true"
    >
      <svg class="plot" id="graph_cluster_4"></svg>
    </b-modal>
  </div>
</template>

<script>
    import {draw, clear} from '../utils/visualization';

    export default {
        name: "ClusterVisualization",
        props: {
            properties: Array,
            cluster_data: Object,
            cluster_id: String,
            clustering_id: String,
            parent_tab: String,
            association: String,
        },
        methods: {
            getGraphLink() {
                return `/job/${this.$root.job.job_id}/cluster/${this.clustering_id}/${this.cluster_id}`;
            },

            draw(graph_parent, svg_name) {
                draw(this.$refs['visualization_popup'], graph_parent, svg_name, "svg#graph_cluster_4");
            },

            async getGraphData(type) {
                if (this.parent_tab && this.$root.$children[0].$refs['formWizard'].activeTabIndex !== this.$root.$children[0].steps.indexOf(this.parent_tab))
                    return;

                const vm = this;

                clear('graph_cluster_1');
                clear('graph_cluster_2');
                clear('graph_cluster_3');

                if (this.association)
                    this.$refs.vis_collapse_1.show = false;

                setTimeout(function () {
                    vm.scrollTo('vis_collapse_1');
                }, 100);

                const properties = this.properties.map(prop => {
                    const resource = this.$root.getResourceById(prop[0]);
                    return {
                        dataset: resource.dataset_id,
                        entity_type: resource.collection_id,
                        property: prop[1],
                    };
                });

                const data = await this.$root.getClusterGraphs(this.clustering_id, this.cluster_id, {
                    cluster_data: this.cluster_data,
                    properties: properties,
                    get_cluster: !Boolean(this.association) || type === 'cluster',
                    get_reconciliation: this.cluster_data.extended === 'yes',
                    associations: this.cluster_data.extended === 'yes' ? this.association : '',
                });

                if (data.cluster_graph)
                    this.draw(data.cluster_graph, "svg#graph_cluster_1");

                if (data.cluster_graph_compact)
                    this.draw(data.cluster_graph_compact, "svg#graph_cluster_2");

                if (data.reconciliation_graph)
                    this.draw(data.reconciliation_graph, "svg#graph_cluster_3");
            },

            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior': 'smooth', 'block': 'start'});
            },
        },
        mounted() {
            if (this.cluster_id)
                this.getGraphData();
        },
        watch: {
            cluster_id() {
                this.getGraphData();
            },
        },
    }
</script>

<style scoped>
  .plot {
    width: 100%;
    height: 800px;
    background-color: #FFFFE0;
  }

  div.tooltip {
    position: absolute;
    background-color: white;
    max-width: 200px;
    height: auto;
    padding: 1px;
    border-style: solid;
    border-radius: 4px;
    border-width: 1px;
    box-shadow: 3px 3px 10px rgba(0, 0, 0, .5);
    pointer-events: none;
  }

  .links line {
    stroke: #999;
    stroke-opacity: 0.6;
  }

  .nodes circle {
    stroke: #fff;
    stroke-width: 1.5px;
  }

  text {
    font-family: sans-serif;
    font-size: 14px;
  }
</style>