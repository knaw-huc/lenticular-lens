import {
    drag, // d3-drag
    scaleOrdinal, // d3-scale
    select, // d3-selection
    pointer, // d3-selection
    schemeCategory10, // d3-scale-chromatic
    forceSimulation, // d3-force
    forceLink, // d3-force
    forceManyBody, // d3-force
    forceCenter // d3-force
} from 'd3';

const color = scaleOrdinal(schemeCategory10);
const factor = x => Math.log2(x + 1) * 16;
const radius = node => node.nodes ? factor(node.nodes) + 2 : node.size * 1.2;

export function draw(canvasContainer, graphData) {
    const container = select(canvasContainer);
    const canvas = container.select('canvas').size() ? container.select('canvas') : container.append('canvas');
    const ctx = canvas.node().getContext('2d');

    let rect, currentChild, selectedNode, clickedNode;
    const root = _ => currentChild || graphData;
    const isSelected = node => selectedNode && (selectedNode === node);
    const isClicked = node => clickedNode && (clickedNode === node);

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const simulation = forceSimulation()
        .force('link', forceLink()
            .id(link => link.id)
            .distance(link => {
                if (link.dist_factor)
                    return factor(link.dist_factor[0]) + factor(link.dist_factor[1]) + link.distance * 0.8;
                return link.distance;
            })
        )
        .force('charge', forceManyBody())
        .force('center', forceCenter(rect.width / 2, rect.height / 2));

    const dragEvent = drag()
        .subject(findNode)
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded);

    canvas.call(dragEvent);
    canvas.on('dblclick', onDblClick);

    updateSimulation();

    function resizeCanvas() {
        canvas.attr('width', 0).attr('height', 0);
        rect = container.node().getBoundingClientRect();
        canvas.attr('width', rect.width).attr('height', rect.height);
        draw();
    }

    function updateSimulation() {
        simulation.nodes(root().nodes).on('tick', draw);
        simulation.force('link').links(root().links);
    }

    function draw() {
        ctx.save();
        ctx.clearRect(0, 0, rect.width, rect.height);

        ctx.fillStyle = '#FFFFE0';
        ctx.fillRect(0, 0, rect.width, rect.height);
        ctx.fill();

        root().links.forEach(link => drawLink(link));
        root().nodes.forEach(node => drawNode(node));

        ctx.restore();
    }

    function findNode(e, position) {
        const x = (position ? position[0] : e.x);
        const y = (position ? position[1] : e.y);

        return root().nodes.find(node => {
            const dx = x - node.x;
            const dy = y - node.y;
            const r = radius(node);

            return (dx * dx + dy * dy) < (r * r);
        });
    }

    function drawLink(link) {
        ctx.beginPath();

        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);

        ctx.lineWidth = Math.sqrt(link.value) + 1;
        ctx.strokeStyle = link.strength < 1 ? 'red' : link.color || 'black';
        ctx.setLineDash(link.dash ? link.dash.split(',') : [3, 20 * (1 - link.strength)]);

        ctx.stroke();
    }

    function drawNode(node) {
        drawNodeOuterCircle(node);
        drawNodeInnerCircle(node);
        drawNodeMissingLinks(node);
        drawNodeLabels(node);
    }

    function drawNodeOuterCircle(node) {
        if (node.investigated && (node.nodes || node.size > 5)) {
            ctx.beginPath();

            ctx.arc(node.x, node.y, radius(node), 0, 2 * Math.PI);

            ctx.fillStyle = 'white';
            ctx.lineWidth = 4;
            ctx.strokeStyle = isSelected(node) || isClicked(node) ? 'red' : 'black';
            ctx.setLineDash(node.satellite ? [10, 3] : [10, 0]);

            ctx.stroke();
            ctx.fill();
        }
    }

    function drawNodeInnerCircle(node) {
        ctx.beginPath();

        const radius = node.nodes ? factor(node.nodes) : node.size || 5;
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);

        ctx.fillStyle = isSelected(node) ? 'red' : color(node.group);
        ctx.lineWidth = 2;
        ctx.strokeStyle = (node.investigated || (!node.nodes && node.size > 5)) ? 'white' : 'black';
        ctx.setLineDash(node.satellite ? [10, 3] : [10, 0]);

        ctx.stroke();
        ctx.fill();
    }

    function drawNodeMissingLinks(node) {
        if (!node.missing_links) return;

        ctx.beginPath();
        ctx.moveTo(node.x, node.y);

        const radius = node.nodes ? factor(node.nodes) * 0.7 : 0;
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI * -node.missing_links, true);
        ctx.fillStyle = 'white';

        ctx.lineTo(node.x, node.y);
        ctx.fill();
    }

    function drawNodeLabels(node) {
        const defaultFont = '12px sans-serif';
        ctx.fillStyle = 'black';

        const labelPosition = node.x + (node.nodes ? factor(node.nodes) : node.size) * 0.9 + 8;

        ctx.font = defaultFont;
        ctx.fillText(node.label || node.id, labelPosition, node.y + 3);

        if (node.nodes) {
            const nodeSizeLabelPosition = node.x + (node.nodes > 2 ? -factor(node.nodes) / 3 : -10);

            ctx.font = 'bold ' + defaultFont;
            ctx.fillText('N:' + node.nodes, nodeSizeLabelPosition, node.y + 3);

            if (node.nodes > 2) {
                const noLinks = node.nodes * (node.nodes - 1) / 2;
                const linkLabel = node.missing_links > 0
                    ? 'L:' + Math.round(noLinks * (1 - node.missing_links)) + "/" + noLinks
                    : 'L:' + noLinks;
                const linkSizeLabelPosition = node.x + (-factor(node.nodes) / 3);

                ctx.font = defaultFont;
                ctx.fillText(linkLabel, linkSizeLabelPosition, node.y + 15);
            }

            if (node.strength && node.nodes > 1) {
                const strengthLabel = Number.parseFloat(String(node.strength))
                    ? 'S:' + Math.round(node.strength * 1000) / 1000
                    : 'S:' + node.strength;

                ctx.font = 'bold ' + defaultFont;
                ctx.fillText(strengthLabel, node.x - 8, node.y + factor(node.nodes) + 13);
            }
        }
    }

    function dragStarted(e) {
        if (!e.active) simulation.alphaTarget(0.2).restart();

        e.subject.fx = e.x;
        e.subject.fy = e.y;
    }

    function dragged(e) {
        e.subject.fx = e.x;
        e.subject.fy = e.y;
    }

    function dragEnded(e) {
        if (!e.active) simulation.alphaTarget(0);
    }

    function onDblClick(e) {
        const xy = pointer(e)
        const node = findNode(e, xy);
        if (!node) return;

        currentChild = node.child;
        updateSimulation();
    }
}