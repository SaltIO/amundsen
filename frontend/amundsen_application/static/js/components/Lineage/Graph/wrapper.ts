import React from 'react';
import ReactDOM from 'react-dom';
import { Lineage } from 'interfaces';
// import { select } from 'd3-selection';
// import chart, { LineageChart } from './chart';
// import chart, { LineageChart } from './dag';
import LineageChart from './LineageChart';
import { Dimensions, Labels } from './types';

const actions = {
  create: (
    el: HTMLElement,
    lineage: Lineage,
    dimensions: Dimensions,
    labels: Labels
  ) => {
    ReactDOM.render(
      React.createElement(LineageChart, { lineage, dimensions, labels }),
      el
    );
  },
  destroy: (el: HTMLElement) => {
    ReactDOM.unmountComponentAtNode(el);
  },
};

export default actions;