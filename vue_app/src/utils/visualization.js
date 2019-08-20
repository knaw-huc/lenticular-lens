import * as d3 from 'd3';

export function draw(popup, graph_parent, svg_name, svg_name_child) {
    var pi = Math.PI;
    var radius2 = 20;

    var selected_node, clicked_node, graph_child = null;
    var color = d3.scaleOrdinal(d3.schemeCategory10);

    var svg = d3.select(svg_name);
    var svg_child = d3.select(svg_name_child);
    var simulation_parent = simulator(svg);
    var simulation_child;

    var tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    update(svg, graph_parent, simulation_parent);


    // FUNCTION FOR SETTING THE SIZE OF COMPACT NODES
    function factor(x) { return Math.log2(x + 1) * 16; }


    // FUNCTION FOR CALCULATING THE ARC REPRESENTING THE MISSING LINKS IN A COMPACT NODE
    function arc(r) {
        return d3.arc()
            .innerRadius(0)
            .outerRadius(function (d) {
                if (d.nodes) return factor(d.nodes) * 0.7;
                if (d.size) return 0;
            })
            .startAngle(0) //converting from degs to radians
            .endAngle(function (d) {
                if (d.missing_links) return -d.missing_links * pi * 2;
                else return 0;
            });
    }


    function update(svg_input, json_graph, rest_simulation) {
        // AT START, CLEAN THE ELEMENTS OF THE GRAPH, IF ANY
        svg_input.selectAll("g").remove();

        var link = null, node = null;
        var rect = svg_input.node().getBoundingClientRect();

        link = svg_input.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(json_graph.links)
            .enter().append("line")
            .style("stroke-width", function (d) { return Math.sqrt(d.value) + 1; })
            .style("stroke", function (d) {
                if (d.strength < 1) return "red";
                else if (d.color) return d.color;
                else return "black";
            })
            .style("stroke-dasharray", function (d) {
                if (d.dash) return d.dash;
                else return "3," + String(20 * (1 - d.strength));
            })
            //// DISPLAY THE STRENGTH OF A LINK
            .on('mouseover.tooltip', function (d) {
                tooltip.transition()
                    .duration(300)
                    .style("opacity", .8);
                tooltip.html(function () {
                    var msg = "";
                    if (d.strength) msg = "&nbsp Strength: " + d.strength + "&nbsp<br>";
                    if (d.count) msg += "&nbsp Links: " + d.count + "&nbsp";
                    return msg;
                })
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY + 10) + "px");
            })
            .on("mouseout.tooltip", function () {
                tooltip.transition()
                    .duration(100)
                    .style("opacity", 0);
            });

        link.exit().remove();

        // ADD THE NODES TO THE GRAPH ACCORDING TO THE GIVEN GRAPH
        node = svg_input.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(json_graph.nodes)
            .enter().append("g");

        ////// OUTER CIRCLE
        node.append("circle")
            .attr("r", function (d) {
                // IF IT IS A COMPACT PLOT AND IT IS NOT INVESTIGATED,
                // THEN RETURN RADIUS ZERO SINCE NO OUTER CIRCLE IS NEEDED
                if ((d.investigated) && (String(d.investigated) === 'false')) return 0;
                // OTHERIWSE, IF IT IS A COMPACT PLOT AND IT IS INVESTIGATED,
                // THEN USERS THE FACTOR FUNCTION PLUS TO TWO
                if (d.nodes) return factor(d.nodes) + 2;
                // OTHERWISE, IF IT IS NOT COMPACT PLOT AND IT IS INVESTIGATED (SIZE > 5)
                if (d.size > 5) return d.size * 1.2;
                return 0;
            })
            .attr("fill", "white")
            .style("stroke", function (d) {
                // IF THE NODE HAS BEEN SET AS SELECTED (IN DOUBLE CLICK)
                // SET THE STROKE TO RED, OTHERWISE, USE BLACK
                if ((selected_node) && (d === selected_node)) return "red";
                else if ((clicked_node) && (d === clicked_node)) return "red";
                return "black";
            })
            .style("stroke-width", 4)
            .style("stroke-dasharray",
                function (d) {
                    if (d.satellite) {return ("10,3");} else {return ("10,0");}
                });

        node.append("circle")
            .attr("r", function (d) {
                // IF IT IS A NODE IN A COMPACT PLOT, USE THE FACTOR FUNCTION TO DETERMINE THE SIZE
                if (d.nodes) return factor(d.nodes);
                // OTHERWISE USE THE SIZE THAT IS GIVEN
                if (d.size) return d.size;
                // OTHERWISE USE 5
                else return 5;
            })
            .attr("fill", function (d) {
                // IF THE NODE HAS BEEN SET AS SELECTED (IN DOUBLE CLICK)
                // SET IT TO RED, OTHERWISE, USE THE GROUP TO CHOOSE A COLOR
                if ((selected_node) && (d === selected_node)) return "red";
                else return color(d.group);
            })
            .on("dblclick", d => node_dblclick(svg_input, d))
            // .on("contextmenu", node_mousedown)
            .style("stroke", function (d) {
                // ADD A WHITE STROKE FOR THE INNER CIRCLE OF NODES IN AN INVESTIGATED CLUSTER
                if ((d.investigated) && (String(d.investigated) === 'true')) return "white";
                // OTHERWISE, IF IT IS A COMPACT PLOT, MAKE IT BLACK
                else if (d.nodes) return "black";
                // OTHERWISE, IF IT IS NOT A COMPACT PLOT, THE NOES ORIGINALLY DID NOT HAVE THE PROPERTY 'INVESTIGATED'
                // THEN WE USE THE SIZE OF THE NODES, WHICH WOULD BE BIGGER THAN SIZE 5 (OF THE ASSOCIATED CLUSTER)
                // SO, ADD A WHITE STROKE FOR THE INNER CIRCLE OF NODES IN AN INVESTIGATED CLUSTER (SIZE > 5)
                else if (d.size > 5) return "white";
                // OTHERWISE, MAKE IT BLACK
                else return "black";
            })
            .style("stroke-width", 2)
            .call(d3.drag()
                .on("start", d => dragstarted(svg_input, d))
                .on("drag", dragged)
                .on("end", d => dragended(svg_input, d)));

        // ADDING THE WHITE ARC INSIDE THE COMPACT NODE REPRESENTING THE MISSING LINKS
        node.append("path")
            .attr("d", arc(radius2))
            .attr("fill", "white");

        // TEXT DISPLAYING INSIDE THE COMPACT NODE THE NUMBER OF NODES WITHIN IT
        node.append("text")
            .text(function (d) {
                if (d.label) return d.label;
                else return d.id;
            })
            .attr('x', function (d) {
                if (d.nodes) return factor(d.nodes) * 0.9 + 8;
                if (d.size) return (d.size * 0.9 + 8);
            })
            .attr('y', 3);

        // TEXT DISPLAYING INSIDE THE COMPACT NODE THE NUMBER OF NODES WITHIN IT
        // COMPACT NODE SIZE TEXT AND POSITION
        node.append("svg:text")
            .attr("dx", function (d) {
                if ((d.nodes) && (d.nodes > 2)) {
                    // return - 8
                    // var label = "N:" + d.node
                    // var radius = factor(d.nodes)
                    return -factor(d.nodes) / 3;
                }
                // FOR SIZE < 2
                // PULLS BACK THE NODE INNER TEXT FROM GOING TO THE RIGHT
                else return -10;
            })
            .attr('dy', 3)
            .text(function (d) {
                if (d.nodes) return "N:" + d.nodes;
            })
            .style("font-weight", "bold");


        // TEXT DISPLAYING INSIDE THE NODE THE TOTAL OF LINKS
        // AND THE LINKS MISSING WITHIN A COMPACT NODE
        // COMPACT TOTAL LINK COUNT AND POSITION
        node.append("svg:text")
            .attr("dx", function (d) {
                if ((d.nodes) && (d.nodes > 2)) {
                    var label;
                    var total = (d.nodes * (d.nodes - 1) / 2);
                    // var center = d3.select(this).attr("cx")
                    if (d.missing_links > 0)
                        label = "L:" + Math.round(total * (1 - d.missing_links)) + "/" + total;
                    else label = "L:" + total;
                    // return - (label.length/2) * 7
                    return -factor(d.nodes) / 3;
                }
            })
            .attr('dy', 15)
            .text(function (d) {
                if ((d.nodes) && (d.nodes > 2)) {
                    var total = (d.nodes * (d.nodes - 1) / 2);
                    if (d.missing_links > 0)
                        return "L:" + Math.round(total * (1 - d.missing_links)) + "/" + total;
                    else return "L:" + total;
                }
            });

        // TEXT DISPLAYING THE STRENGTH OF COMPACT NODES BELLOW THE NODE
        node.append("svg:text")
            .attr("dx", -8)
            .attr('dy', function (d) {
                if (d.nodes) return factor(d.nodes) + 13;
            })
            .text(function (d) {
                if ((d.strength) && ((d.nodes) && (d.nodes > 1)))
                    if (Number.parseFloat(String(d.strength)))
                        return "S:" + Math.round(d.strength * 1000) / 1000;
                    else return "S:" + d.strength;
            })
            .style("font-weight", "bold");

        // METADATA OF THE NODE TO BE DISPLAYED ON MOUSE OVER
        node.append("title")
            .text(function (d) { return d.id; });

        node.exit().remove();

        rest_simulation.nodes(json_graph.nodes).on("tick", ticked);
        rest_simulation.force("link").links(json_graph.links);

        function ticked() {
            link.attr("x1", function (d) { return d.source.x; })
                .attr("y1", function (d) { return d.source.y; })
                .attr("x2", function (d) { return d.target.x; })
                .attr("y2", function (d) { return d.target.y; });

            node.attr("cx", function (d) { return d.x = Math.max(10, Math.min(rect.width - 200, d.x)); })
                .attr("cy", function (d) { return d.y = Math.max(10, Math.min(rect.height - 10, d.y)); })
                .attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
        }

    }

    // CHILD'S NON COMPACT PLOT
    function new_plot(child_graph) {
        graph_child = child_graph;
        clear(svg_child);

        popup.$on('shown', () => {
            simulation_child = simulator(svg_child);
            update(svg_child, child_graph, simulation_child);
        });

        popup.show();
    }

    // D3 GRAPH FORCE SIMULATOR
    function simulator(svg_input) {
        var rect = svg_input.node().getBoundingClientRect();

        return d3.forceSimulation()
            .force("link", d3.forceLink().id(function (d) { return d.id; })
                .distance(
                    function (d) {
                        if (d.dist_factor)
                            return factor(d.dist_factor[0]) + factor(d.dist_factor[1]) + d.distance * 0.8;
                        else return d.distance;
                    })
            )
            .force("charge", d3.forceManyBody())
            .force("center", d3.forceCenter(rect.width / 2, rect.height / 2));
    }

    // ON MOUSE DOWN FUNCTION
    function node_dblclick(svg_input, d) {
        //d.fixed = true;
        selected_node = d;
        if (d.child) {
            // for compact with child, expand
            //selected_node = d;
            if (svg_input === svg)
                update(svg, graph_parent, simulation_parent);
            else if (svg_input === svg_child)
                update(svg_child, graph_child, simulation_child);

            new_plot(d.child);
        } else {
            //selected_node = d;
            if (svg_input === svg)
                update(svg, graph_parent, simulation_parent);
            else if (svg_input === svg_child)
                update(svg_child, graph_child, simulation_child);
        }
    }

    function dragstarted(svg_input, d) {
        if (!d3.event.active) {
            if (svg_input === svg)
                simulation_parent.alphaTarget(0.2).restart(graph_parent);
            else if (svg_input === svg_child)
                simulation_child.alphaTarget(0.2).restart(graph_child);
        }

        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(svg_input, d) {
        if (!d3.event.active)
            if (svg_input === svg)
                simulation_parent.alphaTarget(0);
            else if (svg_input === svg_child)
                simulation_child.alphaTarget(0);

        //d.fx = null;
        //d.fy = null;
    }
}

export function clear(svg) {
    svg = (typeof svg === 'string') ? d3.select(svg) : svg;
    svg.selectAll("*").remove();
}