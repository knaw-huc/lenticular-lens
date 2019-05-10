<template>
    <div>
        <div class="border p-4 mt-4 bg-light">
            <div class="row">
                <div class="col-auto">
                    <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_1></octicon>
                </div>

                <div class="col" v-b-toggle.cluster_plot_row_1>
                    <div class="row">
                        <div class="col-auto h3 pr-0">Cluster</div>
                        <div class="col-auto pl-0">
                            <button-info popup_title="CLUSTER VISUALIZATION">

                            </button-info>
                        </div>
                    </div>
                </div>

                <div class="col-auto" v-if="$root.$children[0].association" v-b-toggle.cluster_plot_row_1>
                    <button type="button" @click="getGraphData('cluster')" class="btn btn-info">Load Original Clusters</button>
                </div>
            </div>
            <b-collapse
                    :visible="!Boolean($root.$children[0].association)"
                    id="cluster_plot_row_1"
                    class="row mb-3"
                    ref="vis_collapse_1"
            >
                <div id="cluster_plot_col_1" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
                    <svg class="plot" id="graph_cluster_1" width="2000" height="800" style="background-color:#FFFFE0;"></svg>
                </div>

                <div class="col pt-4">
                    <div class="row justify-content-end">
                        <div class="col-auto">
                            <a :href="'/job/' + $root.$children[0].job_id + '/cluster/' + $root.$children[0].job_data.results.clusterings[0].clustering_id + '/' + $root.$children[0].cluster_id_selected" target="_blank" class="btn btn-info">Open in new tab</a>
                        </div>
                    </div>
                </div>
            </b-collapse>
        </div>
        <div class="border p-4 mt-4 bg-light">
            <div class="row">
                <div class="col-auto">
                    <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_2></octicon>
                </div>

                <div class="col" v-b-toggle.cluster_plot_row_2>
                    <div class="row">
                        <div class="col-auto h3 pr-0">Compact Cluster</div>
                        <div class="col-auto pl-0">
                            <button-info popup_title="CLUSTER VISUALIZATION">

                            </button-info>
                        </div>
                    </div>
                </div>

                <div class="col-auto" v-if="$root.$children[0].association" v-b-toggle.cluster_plot_row_2>
                    <button type="button" @click="getGraphData('cluster')" class="btn btn-info">Load Original Compact Clusters</button>
                </div>
            </div>
            <b-collapse
                    :visible="!Boolean($root.$children[0].association)"
                    id="cluster_plot_row_2"
                    class="row mb-3"
                    ref="vis_collapse_1"
            >
                <div id="cluster_plot_col_2" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
                    <svg class="plot" id="graph_cluster_2" width="2000" height="800" style="background-color:#FFFFE0;"></svg>
                </div>

                <div class="col pt-4">
                    <div class="row justify-content-end">
                        <div class="col-auto">
                            <a :href="'/job/' + $root.$children[0].job_id + '/cluster/' + $root.$children[0].job_data.results.clusterings[0].clustering_id + '/' + $root.$children[0].cluster_id_selected" target="_blank" class="btn btn-info">Open in new tab</a>
                        </div>
                    </div>
                </div>
            </b-collapse>
        </div>
        
        <div v-if="$root.$children[0].association" class="border p-4 mt-4 bg-light">
            <div class="row">
                <div class="col-auto">
                    <octicon name="chevron-down" scale="3" v-b-toggle.cluster_plot_row_3></octicon>
                </div>

                <div class="col" v-b-toggle.cluster_plot_row_3>
                    <div class="row">
                        <div class="col-auto h3 pr-0">Reconciled</div>
                        <div class="col-auto pl-0">
                            <button-info popup_title="RECONCILED CLUSTER VISUALIZATION">

                            </button-info>
                        </div>
                    </div>
                </div>
            </div>
            <b-collapse
                    :visible="Boolean($root.$children[0].association)"
                    id="cluster_plot_row_3"
                    class="row mb-3"
            >
                <div id="cluster_plot_col_3" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
                    <svg class="plot" id="graph_cluster_3" width="2000" height="800" style="background-color:#FFFFE0;"></svg>
                </div>

                <div class="col pt-4">
                    <div class="row justify-content-end">
                        <div class="col-auto">
                            <a :href="'/job/' + $root.$children[0].job_id + '/cluster/' + $root.$children[0].job_data.results.clusterings[0].clustering_id + '/' + $root.$children[0].cluster_id_selected" target="_blank" class="btn btn-info">Open in new tab</a>
                        </div>
                    </div>
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

                ////// NEW CODE
                var pi = Math.PI;
                var radius2 = 20;
                var node_factor = 7;
                function factor(x) {
                    return Math.log2(x+1)*10
                }
                function arc(r) {
                    return d3.arc()
                      .innerRadius(0)
                      .outerRadius(function(d) { if (d.nodes)
                                                    // return d.nodes*node_factor*0.7
                                                    return factor(d.nodes)*0.7
                                                if (d.size)
                                                    return 0 })
                      // .outerRadius(r)
                      .startAngle(0) //converting from degs to radians
                      .endAngle(function(d) { if (d.missing_links) { return -d.missing_links*pi*2 } else { return 0 }  }  );
                    }

                let color = d3.scaleOrdinal(d3.schemeCategory20);

                let simulation = d3.forceSimulation()
                  .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(function(d) {
                      if (d.dist_factor)
                          return factor(d.dist_factor[0])+factor(d.dist_factor[1])+d.distance*0.8
                      else
                          return d.distance;
                  }))
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

                var path = svg.append("svg:g").selectAll("path")
                    .data(graph.links)
                    .enter().append("svg:path")
                    .attr("class", function(d) { return "link " + d.distance; })
                    .attr("id",function(d,i) { return "linkId_" + i; })
                    .attr("marker-end", function(d) { return "url(#" + d.distance + ")"; });


                var linktext = svg.append("svg:g").selectAll("g.linklabelholder").data(graph.links);

                linktext.enter().append("g").attr("class", "linklabelholder")
                     .append("text")
                     .attr("class", "linklabel")
                     .style("font-size", "13px")
                     .attr("x", "50")
                     .attr("y", "-20")
                     .attr("text-anchor", "start")
                    .style("fill","#000")
                     .append("textPath")
                    .attr("xlink:href",function(d,i) { return "#linkId_" + i;})
                     .text(function(d) {
                        return d.distance;
                     });

                let node = svg.append("g")
                    .attr("class", "nodes")
                  .selectAll("g")
                  .data(graph.nodes)
                  .enter().append("g");

                node.append("circle")
                    .attr("r", function(d) {
                        if ((d.investigated)&&(String(d.investigated) == 'false'))
                                      return 0
                                    if (d.nodes)
                                      return factor(d.nodes) + 2;
                                    if (d.size > 5)
                                      return d.size*1.2;
                                    return 0;})
                          .attr("fill", "white")
                          .style("stroke", "black")
                          .style("stroke-width", 3)

                        node.append("circle")
                        .attr("r", function(d) {  if (d.nodes)
                                                    return factor(d.nodes)
                        if (d.size)
                            return d.size;
                        else return 8;
                    })
                    .attr("fill", function(d) { return color(d.group); })
                    .style("stroke", function(d) {  if ((d.investigated)&&(String(d.investigated) == 'true'))
                                  return "white"
                                else if (d.nodes)
                                  return "black"
                                else if (d.size > 5)
                                  return "white"
                                else
                                  return "black"
                      }) ////// NEW CODE
                    .style("stroke-width", 2) ////// NEW CODE
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                ////// NEW CODE
                node.append("path")
                  .attr("d",  arc(radius2) )
                  .attr("fill", "white");
                node.append("text")
                    .text(function(d) {
                      return d.id;
                    })
                    .attr('x', function(d) {
                        if (d.nodes)
                            return factor(d.nodes)*0.9 + 8
                        if (d.size)
                            return (d.size*0.9 + 8) }) ////// NEW CODE)
                    .attr('y', 3);

                node.append("svg:text")
                .attr("dx", function(d){ if ((d.nodes)&&(d.nodes>2))
                                            return -8
                                       else return -8} )
                .attr('dy', 3)
                .text(function(d){ if (d.nodes)
                                      // if (d.nodes>2)
                                      return "N:" + d.nodes
                                      // else return d.nodes
                                    })
                .style("font-weight","bold");

                node.append("svg:text")
                .attr("dx", function(d){ if ((d.nodes)&&(d.nodes>2)) {
                                      var total = (d.nodes*(d.nodes-1)/2)
                                      if (d.missing_links > 0)
                                        return -15
                                      else
                                 return -7
                                }})
                .attr('dy', 15)
                .text(function(d){ if ((d.nodes)&&(d.nodes>2)) {
                                      var total = (d.nodes*(d.nodes-1)/2)
                                      if (d.missing_links > 0)
                                        return "L:" + Math.round(total*(1-d.missing_links)) + "/" + total
                                      else
                                        return "L:" + total
                                }})

                node.append("svg:text")
                .attr("dx", -8)
                .attr('dy', function (d) { if (d.nodes)
                                          return factor(d.nodes)+13 })
                .text( function(d){ if ((d.strength)&&((d.nodes)&&(d.nodes>1)) )
                                      if (Number.parseFloat(String(d.strength)))
                                        return "S:" + Math.round(d.strength*1000)/1000
                                      else
                                        return "S:" + d.strength
                                      })
                .style("font-weight","bold");

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
                if (this.$root.$children[0].$refs['formWizard'].activeTabIndex !== this.$root.$children[0].steps.indexOf(this.parent_tab))
                    return;

                let vm = this;

                d3.select('svg#graph_cluster_1').selectAll("*").remove();
                d3.select('svg#graph_cluster_2').selectAll("*").remove();
                if (type !== 'cluster') {
                    d3.select('svg#graph_cluster_3').selectAll("*").remove();
                }
                if (this.$root.$children[0].association) {
                    this.$refs.vis_collapse_1.show = false;
                }

                setTimeout(function () {
                    vm.scrollTo('vis_collapse_1');
                }, 100);
            // document.getElementById('graph_cluster_1').parentNode.setAttribute('hidden', 'hidden');
            // document.getElementById('graph_cluster_3').parentNode.setAttribute('hidden', 'hidden');
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
                    if (data.cluster_graph_compact) {
                        this.draw(data.cluster_graph_compact, "svg#graph_cluster_2");
                    }
                    if (data.reconciliation_graph) {
                        // document.getElementById('graph_cluster_3').parentNode.removeAttribute('hidden');
                        this.draw(data.reconciliation_graph, "svg#graph_cluster_3");
                    }
                    let plot_col_1 = document.getElementById('cluster_plot_col_1');
                    plot_col_1.scrollLeft = plot_col_1.scrollWidth - plot_col_1.clientWidth;
                    plot_col_1.scrollTop = (plot_col_1.scrollHeight - plot_col_1.clientHeight) / 2;
                    let plot_col_2 = document.getElementById('cluster_plot_col_2');
                    if (plot_col_2) {
                        plot_col_2.scrollLeft = plot_col_2.scrollWidth - plot_col_2.clientWidth;
                        plot_col_2.scrollTop = (plot_col_2.scrollHeight - plot_col_2.clientHeight) / 2;
                    }
                    let plot_col_3 = document.getElementById('cluster_plot_col_3');
                    if (plot_col_3) {
                        plot_col_3.scrollLeft = plot_col_3.scrollWidth - plot_col_3.clientWidth;
                        plot_col_3.scrollTop = (plot_col_3.scrollHeight - plot_col_3.clientHeight) / 2;
                    }
                });
            },
            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior':'smooth', 'block':'start'});
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
            parent_tab: String,
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