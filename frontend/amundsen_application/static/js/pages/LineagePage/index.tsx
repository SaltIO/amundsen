// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { RouteComponentProps } from 'react-router';

import { getFileLineage, getTableLineage } from 'ducks/lineage/reducer';
import { GetTableLineageRequest, GetFileLineageRequest } from 'ducks/lineage/types';

import { Lineage, LineageItem } from 'interfaces';

import { GlobalState } from 'ducks/rootReducer';
import Breadcrumb from 'features/Breadcrumb';

import GraphLoading from 'components/Lineage/GraphLoading';
import GraphContainer from 'components/Lineage/GraphContainer';
import { getTableLineageDefaultDepth } from 'config/config-utils';
import { buildTableKey, buildFileKey } from 'utils/navigation';

import * as Constants from './constants';

const OK_STATUS_CODE = 200;

export interface PropsFromState {
  isLoading: boolean;
  statusCode: number | null;
  lineageTree: Lineage;
}

export interface DispatchFromProps {
  tableLineageGet: (
    key: string,
    depth?: number,
    direction?: string
  ) => GetTableLineageRequest;
  fileLineageGet: (
    key: string,
    depth?: number,
    direction?: string
  ) => GetFileLineageRequest;
}

export interface MatchTableProps {
  cluster: string;
  database: string;
  schema: string;
  table: string;
}

export interface MatchFileProps {
  data_location_type: string;
  data_location_name: string;
  data_location_container: string;
  type: string;
  name: string;
}

export type LineagePageProps = PropsFromState &
  DispatchFromProps &
  RouteComponentProps<MatchTableProps|MatchFileProps>;

function isTableLineage(props: any): props is MatchTableProps {
  return props.cluster !== undefined &&
          props.database !== undefined &&
          props.schema !== undefined &&
          props.table !== undefined;
}

function isFileLineage(props: any): props is MatchFileProps {
  return props.data_location_type !== undefined &&
          props.data_location_name !== undefined &&
          props.data_location_container !== undefined &&
          props.type !== undefined &&
          props.name !== undefined;
}

const PageError = () => (
  <div className="container error-label">
    <Breadcrumb />
    {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
    <label>{Constants.ERROR_MESSAGE}</label>
  </div>
);

export const LineagePage: React.FC<
  LineagePageProps & RouteComponentProps<MatchTableProps|MatchFileProps>
> = ({ isLoading, statusCode, tableLineageGet, fileLineageGet, lineageTree, match }) => {
  const { params } = match;
  const hasError = statusCode !== OK_STATUS_CODE;

  let pageTitle: string = '';
  let defaultDepth: number;
  let rootNode: LineageItem;

  if (isTableLineage(params)) {
    pageTitle = `Lineage Information | ${params.schema}.${params.table}`;
    const [tableKey] = React.useState(buildTableKey(params));
    defaultDepth = getTableLineageDefaultDepth();

    React.useEffect(() => {
      tableLineageGet(tableKey, defaultDepth);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tableKey]);

    rootNode = {
      badges: [],
      type: 'Table',
      lineage_item_detail: {
        database: params.database,
        cluster: params.cluster,
        schema: params.schema,
        name: params.table,
      },
      key: tableKey,
      level: 0,
      parent: null,
      usage: null,
      source: 'a table',
    };
  }
  else if (isFileLineage(params)) {
    pageTitle = `Lineage Information | ${params.type}.${params.name}`;
    const [fileKey] = React.useState(buildFileKey(params));
    defaultDepth = getTableLineageDefaultDepth();

    React.useEffect(() => {
      fileLineageGet(fileKey, defaultDepth);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fileKey]);

    rootNode = {
      badges: [],
      type: 'File',
      lineage_item_detail: {
        type: params.type,
        name: params.name,
        data_location_type: params.data_location_type,
        data_location_name: params.data_location_name,
        data_location_container: params.data_location_container,
      },
      key: fileKey,
      level: 0,
      parent: null,
      usage: null,
      source: 'a file',
    };
  }
  else {
    throw Error("Unknown");
  }

  lineageTree.upstream_entities.push(rootNode);
  lineageTree.downstream_entities.push(rootNode);

  let content: JSX.Element | null = null;

  if (isLoading) {
    content = <GraphLoading />;
  } else if (hasError) {
    content = <PageError />;
  } else {
    content = <GraphContainer rootNode={rootNode} lineage={lineageTree} />;
  }

  return (
    <DocumentTitle title={`${pageTitle}`}>
      {content}
    </DocumentTitle>
  );
};
export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.lineage.isLoading,
  statusCode: state.lineage.statusCode,
  lineageTree: state.lineage.lineageTree,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({
    tableLineageGet: getTableLineage,
    fileLineageGet: getFileLineage
  }, dispatch);

export default connect<PropsFromState, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(LineagePage);
