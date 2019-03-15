<template>
    <div id="cluster_plot_row" class="row" style="background-color:#FFFFE0;" >
        <div id="cluster_plot_col" class="col-md-12" style='height: 40em; width:100%; scroll: both; overflow: auto;' >
            <svg class="plot" id="graph_cluster" width="1000" height="800" style="background-color:#FFFFE0;"></svg>
        </div>
    </div>

</template>

<script>
    import * as d3 from 'd3'

    export default {
        data() {
            return {
                graph: {},
            }
        },
        methods: {
            draw() {
                let svg = d3.select("svg#graph_cluster");

                svg.selectAll("*").remove();

                let width = +svg.attr("width"),
                  height = +svg.attr("height");

                let color = d3.scaleOrdinal(d3.schemeCategory20);

                let simulation = d3.forceSimulation()
                  .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(function(d) {return d.distance;}))
                  .force("charge", d3.forceManyBody())
                  .force("center", d3.forceCenter(width / 2, height / 2));

                let graph = this.graph;

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

                node.append("circle")
                    .attr("r", function(d) { if (d.size)
                                                return d.size;
                                             else return 5; })
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
                      .attr("transform", function(d) {
                        return "translate(" + d.x + "," + d.y + ")";
                      })
                }

                function dragstarted(d) {
                  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
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
            getGraphData() {
                fetch('/job/' + this.$root.$children[0].job_id + '/cluster/' + this.cluster_id + '/graph')
                .then((response) => response.json())
                .then((data) => {
                    this.graph = data.graph;
                    this.draw();
                });
            },
        },
        mounted() {
            if (this.cluster_id) {
                this.getGraphData();
            }
        },
        props: {
            cluster_id: String,
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