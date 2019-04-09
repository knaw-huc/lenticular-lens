<template>
    <div>
        <div class="border p-4 mt-4 bg-light">
            <div class="row">
                <div class="col-auto">
                    <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_1></octicon>
                </div>

                <div class="col" v-b-toggle.cluster_plot_row_1>
                    <div class="row">
                        <div class="col h3">Cluster</div>
                    </div>
                </div>

                <div class="col-auto" v-if="$root.$children[0].association" v-b-toggle.cluster_plot_row_1>
                    <button type="button" @click="getGraphData('cluster')" class="btn btn-info">Get Clusters</button>
                </div>
            </div>
            <b-collapse
                    :visible="!Boolean($root.$children[0].association)"
                    id="cluster_plot_row_1"
                    class="row mb-3"
                    style="background-color:#FFFFE0;"
                    ref="vis_collapse_1"
            >
                <div id="cluster_plot_col_1" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
                    <svg class="plot" id="graph_cluster_1" width="2000" height="800" style="background-color:#FFFFE0;"></svg>
                </div>
            </b-collapse>
        </div>

        <div v-if="$root.$children[0].association" class="border p-4 mt-4 bg-light">
            <div class="row">
                <div class="col-auto">
                    <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_2></octicon>
                </div>

                <div class="col" v-b-toggle.cluster_plot_row_2>
                    <div class="row">
                        <div class="col h3">Reconciled</div>
                    </div>
                </div>
            </div>
            <b-collapse :visible="Boolean($root.$children[0].association)" id="cluster_plot_row_2" class="row mb-3" style="background-color:#FFFFE0;" >
                <div id="cluster_plot_col_2" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
                    <svg class="plot" id="graph_cluster_2" width="2000" height="800" style="background-color:#FFFFE0;"></svg>
                </div>
            </b-collapse>
        </div>
    </div>
</template>

<script>
    import * as d3 from 'd3'

    export default {
        methods: {
            draw(graph, svg_name) {
                let svg = d3.select(svg_name);

                svg.selectAll("*").remove();

                let width = +svg.attr("width"),
                  height = +svg.attr("height");
                let radius = 200;

                let color = d3.scaleOrdinal(d3.schemeCategory20);

                let simulation = d3.forceSimulation()
                  .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(function(d) {return d.distance;}))
                  .force("charge", d3.forceManyBody())
                  .force("center", d3.forceCenter(width / 2, height / 2));

                let link = svg
                    .append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(graph.links)
                    .enter().append("line")
                    .on("click", function() { rejectLink() })
                    .style("stroke-width", function(d) { return Math.sqrt(d.value)+1; })
                    .style("stroke", function(d) { if (d.strenght < 1)
                                                      return "red";
                                                   else if (d.color)
                                                      return d.color;
                                                   else return "black"; })
                    .style("stroke-dasharray", function(d) {  if (d.dash)
                                                                  return d.dash;
                                                              else {
                                                                  let space = String(20*(1-d.strenght));
                                                                  return ("3," + space ) } } );

                let node = svg.append("g")
                    .attr("class", "nodes")
                  .selectAll("g")
                  .data(graph.nodes)
                  .enter().append("g");

                node.append("svg:image")
                    .attr("class", "circle")
                    .attr("xlink:href", function(d) { if (d.size < 6)
                                                return "";
                                             else return "https://github.com/favicon.ico"; })
                    .attr("x", "-12px")
                    .attr("y", "-12px")
                    .attr("width", "24px")
                    .attr("height", "24px");

                node.append("circle")
                    .attr("r", function(d) { if (d.size)
                                                return d.size;
                                             else return 8; })
                    .attr("fill", function(d) { return color(d.group); })
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                node.append("text")
                    .text(function(d) {
                      return d.id;
                    })
                    .attr('x', 6)
                    .attr('y', 3);

                node.append("title")
                    .text(function(d) { return d.id; });

                simulation
                    .nodes(graph.nodes)
                    .on("tick", ticked);

                simulation.force("link")
                    .links(graph.links);

                function ticked() {
                  link
                      .attr("x1", function(d) { return d.source.x; })
                      .attr("y1", function(d) { return d.source.y; })
                      .attr("x2", function(d) { return d.target.x; })
                      .attr("y2", function(d) { return d.target.y; });

                  node
                    .attr("cx", function(d) { return d.x = Math.max(10, Math.min(width - radius, d.x)); })
                    .attr("cy", function(d) { return d.y = Math.max(10, Math.min(height - 10, d.y)); })
                    .attr("transform", function(d) {
                        return "translate(" + d.x + "," + d.y + ")";
                      })
                }

                function dragstarted(d) {
                  if (!d3.event.active) simulation.alphaTarget(0.2).restart();
                  d.fx = d.x;
                  d.fy = d.y;
                }

                function dragged(d) {
                  d.fx = d3.event.x;
                  d.fy = d3.event.y;
                }

                function dragended(d) {
                  if (!d3.event.active) simulation.alphaTarget(0);
                  d.fx = null;
                  d.fy = null;
                }
            },
            getGraphData(type) {
                d3.select('svg#graph_cluster_1').selectAll("*").remove();
                if (type !== 'cluster') {
                    d3.select('svg#graph_cluster_2').selectAll("*").remove();
                }
                if (this.$root.$children[0].association) {
                    this.$refs.vis_collapse_1.show = false;
                }
            // document.getElementById('graph_cluster_1').parentNode.setAttribute('hidden', 'hidden');
            // document.getElementById('graph_cluster_2').parentNode.setAttribute('hidden', 'hidden');
                fetch(
                    '/job/' + this.$root.$children[0].job_id + '/cluster/' + this.clustering_id + '/' + this.cluster_id + '/graph',
                    {
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                            },
                            method: "POST",
                            body: JSON.stringify({
                                'cluster_data': this.cluster_data,
                                'get_cluster': !Boolean(this.$root.$children[0].association) || type === 'cluster',
                                'get_reconciliation': Boolean(this.$root.$children[0].association),
                                'associations': this.$root.$children[0].association,
                            })
                        })
                .then((response) => response.json())
                .then((data) => {
                    if (data.cluster_graph) {
                        // document.getElementById('graph_cluster_1').parentNode.removeAttribute('hidden');
                        this.draw(data.cluster_graph, "svg#graph_cluster_1");
                    }
                    if (data.reconciliation_graph) {
                        // document.getElementById('graph_cluster_2').parentNode.removeAttribute('hidden');
                        this.draw(data.reconciliation_graph, "svg#graph_cluster_2");
                    }
                    let plot_col_1 = document.getElementById('cluster_plot_col_1');
                    plot_col_1.scrollLeft = plot_col_1.scrollWidth - plot_col_1.clientWidth;
                    plot_col_1.scrollTop = (plot_col_1.scrollHeight - plot_col_1.clientHeight) / 2;
                    let plot_col_2 = document.getElementById('cluster_plot_col_2');
                    plot_col_2.scrollLeft = plot_col_2.scrollWidth - plot_col_2.clientWidth;
                    plot_col_2.scrollTop = (plot_col_2.scrollHeight - plot_col_2.clientHeight) / 2;
                });
            },
        },
        mounted() {
            if (this.cluster_id) {
                this.getGraphData();
            }
        },
        props: {
            cluster_data: Object,
            cluster_id: String,
            clustering_id: String,
        },
        name: "ClusterVisualizationComponent",
        watch: {
            cluster_id() {
                this.getGraphData();
            },
        },
    }
</script>

<style scoped>
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
      font-size: 10px;
    }

    .background{
      background-color: lightyellow; }
</style>