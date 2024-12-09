import React, { useRef, useEffect } from 'react';
import { select, Selection } from 'd3-selection';
import * as d3 from 'd3';
import { drag } from 'd3-drag';
import { zoom } from 'd3-zoom';
import { SimulationNodeDatum } from 'd3-force';
import { Lineage, LineageItem } from 'interfaces';
import { Dimensions, Labels } from './types';

interface D3LineageItem extends LineageItem, SimulationNodeDatum {
  direction?: 'upstream' | 'downstream' | 'root';
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface LineageChartProps {
  lineage: Lineage;
  dimensions: Dimensions;
  labels: Labels;
}

const LineageChart: React.FC<LineageChartProps> = ({ lineage, dimensions, labels }) => {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous content to avoid duplication

    const width = dimensions.width;
    const height = dimensions.height;

    const g = svg.append('g');
    const zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoomBehavior);
    svg.attr('viewBox', `0 0 ${width} ${height}`).attr('preserveAspectRatio', 'xMidYMid meet');

    if (hasLineageData(lineage)) {
      const nodesMap = new Map<string, D3LineageItem>();
      const levelGap = 150;
      const nodeGap = 200;
      const nodeRectWidth = 250;
      const nodeRectHeight = 50;
      const textMargin = 10;

      lineage.upstream_entities.forEach((item) => {
        if (!nodesMap.has(item.key)) {
          const direction = item.level === 0 ? 'root' : 'upstream';
          nodesMap.set(item.key, { ...toD3LineageItem(item), direction });
        }
      });

      lineage.downstream_entities.forEach((item) => {
        if (!nodesMap.has(item.key)) {
          const direction = item.level === 0 ? 'root' : 'downstream';
          nodesMap.set(item.key, { ...toD3LineageItem(item), direction });
        }
      });

      const nodes = Array.from(nodesMap.values());
      const links = createLinks(lineage);
      const rootNode = nodes.find((node) => node.level === 0);

      if (!rootNode) throw new Error("Root node not found");

      rootNode.x = width / 2 - nodeRectWidth;
      rootNode.y = height / 2 - nodeRectHeight;

      nodes.forEach((node) => {
        if (node.direction === 'upstream') {
          node.x = (rootNode.x ?? 0) - node.level * nodeGap;
          node.y = (rootNode.y ?? 0) - node.level * levelGap;
        } else if (node.direction === 'downstream') {
          node.x = (rootNode.x ?? 0) + node.level * nodeGap;
          node.y = (rootNode.y ?? 0) + node.level * levelGap;
        } else {
          node.x = rootNode.x ?? 0;
          node.y = rootNode.y ?? 0;
        }
      });

      const collisionRadius = nodeRectWidth / 2 + 10; // Add padding around each node

      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id((d: any) => d.key))
        .force('charge', d3.forceManyBody().strength(-500))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide(collisionRadius))
        .alphaDecay(0.03);  // Slow down the decay to let the nodes settle smoothly

      const link = g.append('g')
        .selectAll('path')
        .data(links)
        .join('path')
        .attr('stroke', '#999')
        .attr('stroke-width', 4)
        .attr('marker-end', 'url(#arrow)')
        .attr('d', (d: any) => drawLinkPath(d, nodeRectWidth, nodeRectHeight));

      const nodeGroup = g.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('transform', (d) => `translate(${d.x}, ${d.y})`)
        .call(drag<SVGGElement, D3LineageItem>()
          .on('start', (event, d) => dragstarted(event, d, simulation))
          .on('drag', dragged)
          .on('end', (event, d) => dragended(event, d, simulation)));

      nodeGroup.append('rect')
        .attr('rx', 5)
        .attr('ry', 5)
        .attr('width', nodeRectWidth)
        .attr('height', nodeRectHeight)
        .attr('fill', (d) => (d.key === rootNode.key ? 'black' : '#DEFF2D'))
        .attr('stroke', (d) => (d.key === rootNode.key ? '#DEFF2D' : 'black'))
        .attr('stroke-width', 2);

      nodeGroup.append('text')
        .attr('text-anchor', 'start')
        .attr('x', textMargin)
        .attr('dy', '1.5em')
        .style('fill', (d) => (d.key === rootNode.key ? '#DEFF2D' : 'black'))
        .text((d) => getSearchLinkText(d))
        .each(function () {
          truncateText(select(this), nodeRectWidth - 2 * textMargin);
        });

      nodeGroup.append('title').text((d) => getTitle(d));

      simulation.on('tick', () => {
        link.attr('d', (d: any) => drawLinkPath(d, nodeRectWidth, nodeRectHeight));
        nodeGroup.attr('transform', (d) => `translate(${d.x}, ${d.y})`);
      });
    }
  }, [lineage, dimensions, labels]);

  return <svg ref={svgRef} width={dimensions.width} height={dimensions.height}></svg>;
};

// Helper functions

// Define the type for each link
type Link = { source: string; target: string; direction: 'upstream' | 'downstream' };

function createLinks(lineage: Lineage): Link[] {
  const links: Link[] = [];
  lineage.upstream_entities.forEach((item) => {
    if (item.parent) {
      links.push({ source: item.key, target: item.parent, direction: 'upstream' });
    }
  });
  lineage.downstream_entities.forEach((item) => {
    if (item.parent) {
      links.push({ source: item.parent, target: item.key, direction: 'downstream' });
    }
  });
  return links;
}


function drawLinkPath(d: any, nodeRectWidth: number, nodeRectHeight: number) {
  const sourceX = d.source.x + nodeRectWidth / 2;
  const sourceY = d.source.y + nodeRectHeight / 2;
  const targetX = d.target.x + nodeRectWidth / 2;
  const targetY = d.target.y + nodeRectHeight / 2;
  return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;
}

function dragstarted(event: any, d: D3LineageItem, simulation: any) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event: any, d: D3LineageItem) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event: any, d: D3LineageItem, simulation: any) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null; // Ensure fx is cleared after drag
  d.fy = null; // Ensure fy is cleared after drag
}

function truncateText(textSelection: Selection<SVGTextElement, any, any, any>, maxWidth: number) {
  let textLength = textSelection.node()?.getComputedTextLength();
  let textContent = textSelection.text();

  while (textLength && textLength > maxWidth && textContent.length > 0) {
    textContent = textContent.slice(0, -1);
    textSelection.text(`${textContent}...`);
    textLength = textSelection.node()?.getComputedTextLength();
  }
}

function hasLineageData(lineage: Lineage) {
  return lineage.downstream_entities.length > 0 || lineage.upstream_entities.length > 0;
}

function toD3LineageItem(item: LineageItem): D3LineageItem {
  return { ...item, x: undefined, y: undefined, fx: null, fy: null };
}

function getSearchLinkText(d: D3LineageItem) {
  if (d.type === 'Table') {
    return `${(d.lineage_item_detail as any).cluster}.${(d.lineage_item_detail as any).schema}`;
  } else if (d.type === 'File') {
    return `${(d.lineage_item_detail as any).data_location_type}.${(d.lineage_item_detail as any).data_location_name}`;
  }
  return '#';
}

function getTitle(d: D3LineageItem) {
  if (d.type === 'Table') {
    return `${(d.lineage_item_detail as any).cluster}.${(d.lineage_item_detail as any).schema}.${(d.lineage_item_detail as any).name}`;
  } else if (d.type === 'File') {
    return `${(d.lineage_item_detail as any).data_location_type}.${(d.lineage_item_detail as any).data_location_name}.${(d.lineage_item_detail as any).name}`;
  }
  return '';
}

export default LineageChart;
