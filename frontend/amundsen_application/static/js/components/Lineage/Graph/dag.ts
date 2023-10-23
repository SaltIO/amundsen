/* eslint-disable no-underscore-dangle, no-param-reassign */


import { d3 } from 'd3';
import { Stratify } from 'd3-dag';
import { hierarchy } from 'd3-hierarchy';
import { zoom as d3Zoom, zoomIdentity } from 'd3-zoom';
import { select, Selection } from 'd3-selection';
import { Lineage, LineageItem } from 'interfaces';
import {
  ANIMATION_DURATION,
  CHART_DEFAULT_DIMENSIONS,
  CHART_DEFAULT_LABELS,
  LINEAGE_SCENE_MARGIN,
  NODE_STATUS_Y_OFFSET,
  NODE_LABEL_X_OFFSET,
  NODE_LABEL_Y_OFFSET,
  UPSTREAM_LABEL_OFFSET,
} from './constants';
import { Coordinates, Dimensions, Labels, TreeLineageNode } from './types';
import { getLink } from 'components/ResourceListItem/TableListItem';

export interface LineageChartData {
  lineage: Lineage;
  dimensions: Dimensions;
  labels: Labels;
}

export interface LineageChart {
  (selection: any): any;
}

// We support up to 1000 direct nodes.
const NODE_LIMIT = 1000;
const ROOT_RADIUS = 12;
const NODE_RADIUS = 8;
const CHARACTER_OFFSET = 10;


/**
 * Confirm presence of nodes to render.
 */
export const hasLineageData = (lineage: Lineage) =>
  lineage.downstream_entities.length > 0 ||
  lineage.upstream_entities.length > 0;

const lc = (): LineageChart => {
  let svg: Selection<SVGSVGElement, any, null, any>;
  let g;

  let dimensions: Dimensions = CHART_DEFAULT_DIMENSIONS;
  let labels: Labels = CHART_DEFAULT_LABELS;
  let lineage: Lineage;

  function renderGraph() {

    const nodes = [...lineage.upstream_entities, ...lineage.downstream_entities];
    const links = nodes.map(node => ({ source: node.parent, target: node.key }));


    const dagStratify = Stratify()
      .id(d => d.key)
      .parentId(d => d.parent_key);

    const dagData = dagStratify(nodes);

    // const width = (dimensions.width - (LINEAGE_SCENE_MARGIN.left + LINEAGE_SCENE_MARGIN.right)) / 2;
    // const height = dimensions.height;


    const svg = d3.select("svg"),
          width = +svg.attr("width"),
          height = +svg.attr("height");

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.key))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2));

    // Drawing links
    const link = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter().append("line");

    // Drawing nodes
    const node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(nodes)
        .enter().append("circle")
        .attr("r", 5);

    // This is the magic part: the force simulation will "tick"
    // and recompute node and link positions, updating the SVG elements.
    simulation.nodes(nodes).on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
    });

    simulation.force("link").links(links);
  }

  const chart = ((
    _selection: Selection<HTMLElement, LineageChartData, any, any>
  ) => {
    _selection.each(function bc(_data: LineageChartData) {
      ({ dimensions, labels, lineage } = _data);

      if (!svg) {
        ({ svg, g } = buildSVG(this, dimensions));
      }

      renderLabels(svg, dimensions, labels);

      if (hasLineageData(lineage)) {
        renderGraph();
      }
    });
  }) as LineageChart;

  return chart;
};

export default lc;
