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
                                        This is an example of links discovered using an approximate string similarity on  <strong>Ecartico</strong>, <strong>Baptism</strong>, <strong>Marriage</strong> and <strong>Burial</strong> for married Amsterdammers between 1600 and 1650. These links are specifically the ones that link different occurrences of <strong>Meulder Hans</strong>.
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
                                        The cluster of <strong>Meulder Hans</strong> is composed of 6 nodes (potentially the same person) using 13 link. The links in plain black represent an exact match (link strength = 1) while those in dotted red represent a link of strength below 1. The color of the node depicts the data-source it is stemmed from. So in this real example cluster,
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
                                <div class="text-left">
                                    <div class="h3">A Compact Representation of Meulder Hans' ILN</div>
                                    <p class="h5 pt-4 pl-5">
                                        The compact representation of a cluster allows for the display of large clusters and a comprehensive aggravation of nodes. The approach groups nodes base on similar link strength starting from the highest strength in the identity network. From the original cluster, two sub-groups of nodes can be identified using the link strength of 1 (black plain link) together.
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
                                        <li>The last information (not present in this example but visible in the second compact example of size 35) removes a percentage of the node's color to indicate the number of missing links for the number of nodes aggregated</li>
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
                                        This is an example of a bigger cluster of size 35 potentially representing <strong>Pieterss Grietje</strong>. The larger an ILN gets, the less comprehensive it is visually. Especially when it highlight a mesh topology. For this very reason, the compact version of the visual ILN is of importance for visual aid for validation purposes.
                                    </p>

                                    <div class="text-center pt-4">
                                        <img src="/static/images/1  Pieters Grietje (Cluster).jpg" width="800"/>
                                    </div>

                                    <p class="h5 pt-4 pl-5">
                                        This is the compact version of a cluster of size 35 potentially representing <strong>Pieterss Grietje</strong>. In this examople, 35 nodes are now converted into 4 compact nodes of size 25, 3, 2 and two. The last two nodes are of size one. The compact node of size 25 is composed of 294 limks insted of 300. Meaning 6 links are missing.
                                    </p>

                                    <div class="text-center pt-4">
                                        <img src="/static/images/2  Pieters Grietje (Cluster-Compact).jpg" width="800"/>
                                    </div>
                                    
                                    <div class="h3 pt-5">Expanding a Compact Node with Double-Click</div>
                                    
                                    <p class="h5 pt-4 pl-5">
                                        For a better validation experience, each of the compact nodes can be expanded. This allows a detailed understanding on the type of network (START - LINE - MESH) that defines the aggragated node. When a compact node (sub-cluster) is double-clicked, for example the one of size 3, it is highlighted in red as shown in on the left side the figure below, and its expanded version is ploted, as shown in the right side of the figure.
                                    </p>

                                    <div class="text-center pt-4">
                                        <img src="/static/images/3 Meulder Hans (Cluster-Compact Selected).jpg" width="1000"/>
                                    </div>
                                </div>
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
                                <div class="text-left">
                                    <div class="h2">Reconciling an ILN</div>
                                    
                                    <p class="h5 pt-4 pl-5">
                                        We enable the reconciliation of an ILN using relations between discovered ILN. For the current example, the relation used is the marital status meaning married people. In this example, the ILN to reconcile is the one of <strong>Meulder Hans</strong>. It is the one in <strong>blue</strong> and it connect to two other clusters using purple dotted lines. Reading the graph, the other two clusters indicate that <strong>Meulder Hans</strong> appears to be connected to two women: **Petsinck Catharina (orange)<strong> and </strong>Jans Fijtje (green)**.
                                    </p>
                                    
                                    <p class="h5 pt-4 pl-5">
                                        We provide two representation where the first picture presents a compact representation of all clusters while the second representation presents a non compact representation of the investigated cluster: <strong>Meulder Hans</strong>.
                                    </p>
                                    
                                    <p class="h5 pt-4 pl-5">
                                        Now, given this additional marital status, is it plausible that all nodes representing <strong>Meulder Hans</strong> are indeed representing the same person?
                                    </p>
                                    
                                    <p class="h5 pt-4 pl-5">
                                        To answer this questions, we make use of the existence of <strong>cycle</strong> to materialise strong evidence.
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