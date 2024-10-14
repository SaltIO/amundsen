// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { logClick } from 'utils/analytics';

import { ResourceType, TableMetadata } from 'interfaces';

import { exportEnabled } from 'config/config-utils';

import './styles.scss';

import Papa from 'papaparse';

interface StateFromProps {
  tableData: TableMetadata;
}

export type ExportMetadataIconProps = StateFromProps;

export class ExportMetadataIcon extends React.Component<ExportMetadataIconProps> {

  triggerDownload = (csv, filename) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  handleClick = (e: React.MouseEvent<HTMLElement>) => {
    e.stopPropagation();
    e.preventDefault();

    const { tableData } = this.props;

    const exportedMetadata: Record<string, any>[] = [];

    if (tableData) {

      tableData.columns.forEach(column => {
        let rowData: Record<string, any> = {};
        rowData['column_key'] = column.key;
        rowData['column_name'] = column.name;
        rowData['column_data_type'] = column.col_type;
        rowData['column_description'] = column.description;
        let column_badges: string[] = [];
        column.badges.forEach(badge => {
          if (badge.badge_name) {
            column_badges.push(badge.badge_name);
          }
        });
        rowData['column_badges'] = column_badges;

        exportedMetadata.push(rowData);
      });

      const csv = Papa.unparse(exportedMetadata);
      this.triggerDownload(csv, `export_metadata.${tableData.database}.${tableData.cluster}.${tableData.schema}.${tableData.name}.csv`);
    }


    logClick(e, {
      label: 'Export Metadata',
      target_id: `export-metadata-button`,
    });
  };

  render() {
    const { tableData } = this.props;

    return (
      <div
        className={'export-metadata-icon'}
        onClick={this.handleClick}
      >
        <img
          className={
            'icon icon-export-metadata'
          }
          alt=""
        />
      </div>
    );
  }
}

export default ExportMetadataIcon;