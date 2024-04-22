// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import { ResourceType, Lineage, LineageItem, TableLineageItemDetail, FileLineageItemDetail, isTableLineageItemDetail, isFileLineageItemDetail  } from 'interfaces';
import { getSourceIconClass } from 'config/config-utils';
import { getLink as getTableLink } from 'components/ResourceListItem/TableListItem';
import { getLink as getFileLink } from 'components/ResourceListItem/FileListItem';
import Graph from 'components/Lineage/Graph';

import './styles.scss';

const CONTAINER_TITLE = 'Lineage Graph';
const BACK_TABLE_LINK = 'Back to table details';

export interface GraphContainerProps {
  lineage: Lineage;
  rootNode: LineageItem;
}

export const GraphContainer: React.FC<GraphContainerProps> = ({
  lineage,
  rootNode,
}: GraphContainerProps) => {
  let rootTitle = 'UNKNOWN RESOURCE';
  if (isTableLineageItemDetail(rootNode.lineage_item_detail) {
    rootTitle = `${(rootNode.lineage_item_detail as TableLineageItemDetail).schema}.${(rootNode.lineage_item_detail as TableLineageItemDetail).name}`;
  }
  else if (isFileLineageItemDetail(rootNode.lineage_item_detail) {
    rootTitle = `${(rootNode.lineage_item_detail as FileLineageItemDetail).type}.${(rootNode.lineage_item_detail as FileLineageItemDetail).name}`;
  }

  return (
    <div className="resource-detail-layout">
      <header className="resource-header">
        <div className="header-section">
          <span
            className={
              'icon icon-header ' +
              (isTableLineageItemDetail(rootNode.lineage_item_detail) ?
                  getSourceIconClass((rootNode.lineage_item_detail as TableLineageItemDetail).database, ResourceType.table)
                  :
                  isFileLineageItemDetail(rootNode.lineage_item_detail) ?
                    getSourceIconClass((rootNode.lineage_item_detail as FileLineageItemDetail).type, ResourceType.file)
                    :
                    ''
              )
            }
          />
        </div>
        <div className="header-section header-title">
          <h1 className="header-title-text truncated" title={rootTitle}>
            {rootTitle}
            <span className="lineage-graph-label">{CONTAINER_TITLE}</span>
          </h1>
          <div className="lineage-graph-backlink">
            <Link
              className="resource-list-item table-list-item"
              to={
                (isTableLineageItemDetail(rootNode.lineage_item_detail) ?
                    getTableLink({ key: rootNode.key, ...rootNode.lineage_item_detail}, 'table-lineage-page')
                    :
                    isFileLineageItemDetail(rootNode.lineage_item_detail) ?
                      getFileLink({ key: rootNode.key, ...rootNode.lineage_item_detail}, 'table-lineage-page')
                      :
                      ''
                )
              }
            >
              {"Back to Details..."}
            </Link>
          </div>
        </div>
        <div className="header-section header-links">
          <Link
            to={
              (isTableLineageItemDetail(rootNode.lineage_item_detail) ?
                  getTableLink(rootNode, 'table-lineage-page')
                  :
                  isFileLineageItemDetail(rootNode.lineage_item_detail) ?
                    getFileLink(rootNode, 'table-lineage-page')
                    :
                    ''
              )
            }
            className="btn btn-close clear-button icon-header"
          />
        </div>
      </header>
      <div className="graph-container">
        <Graph lineage={lineage} />
      </div>
    </div>
  );
};

export default GraphContainer;
