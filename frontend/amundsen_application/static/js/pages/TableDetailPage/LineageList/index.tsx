// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0
import * as React from 'react';

import {
  getTableLineageDisableAppListLinks,
  getTableLineageConfiguration,
} from 'config/config-utils';
import { ResourceType, TableResource, FileResource } from 'interfaces/Resources';
import { LineageItem, TableLineageItemDetail, FileLineageItemDetail } from 'interfaces/Lineage';
import TableListItem from 'components/ResourceListItem/TableListItem';
import FileListItem from 'components/ResourceListItem/FileListItem';
import { getHighlightedTableMetadata, getHighlightedFileMetadata } from 'components/ResourceListItem/MetadataHighlightList/utils';

import { TableMetadata } from 'interfaces/TableMetadata';
import ReactMarkdown from 'react-markdown';
import { NO_LINEAGE_INFO } from '../constants';

import './styles.scss';
import { getOwnerItemPropsFromUsers } from 'utils/owner';

export interface LineageListProps {
  items: LineageItem[];
  direction: string;
  tableDetails?: TableMetadata;
}

const isTableLinkDisabled = (table: LineageItem) => {
  // check if item is currently indexed in Amundsen, if it's not mark as disabled
  if (table.in_amundsen === false) {
    return true;
  }

  // use configuration to determine weather a table link is disabled or not
  const disableAppListLinks = getTableLineageDisableAppListLinks();
  let disabled = false;

  if (disableAppListLinks) {
    disabled = Object.keys(disableAppListLinks).some((key) => {
      if (key === 'badges') {
        return (
          table.badges.filter(({ badge_name }) =>
            disableAppListLinks?.badges?.some((badge) => badge_name === badge)
          ).length === 0
        );
      }

      return disableAppListLinks![key].test(table[key]) === false;
    });
  }

  return disabled;
};

const LineageListMessage: React.FC<{ message: string }> = ({ message }) => (
  <div className="lineage-message">
    <ReactMarkdown
      allowDangerousHtml
      linkTarget="_blank"
      className="message-text"
    >
      {message}
    </ReactMarkdown>
  </div>
);

export const LineageList: React.FC<LineageListProps> = ({
  items,
  direction,
  tableDetails,
}: LineageListProps) => {
  if (items.length === 0) {
    return (
      <div className="resource-list">
        <div className="empty-message body-placeholder">{NO_LINEAGE_INFO}</div>
      </div>
    );
  }
  const { inAppListMessageGenerator } = getTableLineageConfiguration();

  const message =
    tableDetails &&
    inAppListMessageGenerator?.(
      direction,
      tableDetails.database,
      tableDetails.cluster,
      tableDetails.schema,
      tableDetails.name
    );

  return (
    <>
      <div className="list-group">
        {items.map((item, index) => {

          if (item.type == 'Table') {
            const logging = {
              index,
              source: `table_lineage_list_${direction}`,
            };

            const table = item.lineage_item_detail as unknown as TableLineageItemDetail;
            const tableResource: TableResource = {
              key: item.key,
              badges: item.badges,
              database: table.database,
              cluster: table.cluster,
              schema: table.schema,
              name: table.name,
              type: ResourceType.table,
              description: '',
            };

            return (
              <TableListItem
                table={tableResource}
                logging={logging}
                key={`lineage-item::${index}`}
                tableHighlights={getHighlightedTableMetadata(tableResource)}
                disabled={isTableLinkDisabled(item)}
              />
            );
          }
          else if (item.type == 'File') {
            const logging = {
              index,
              source: `file_lineage_list_${direction}`,
            };
            const file = item.lineage_item_detail as unknown as FileLineageItemDetail;
            const fileResource: FileResource = {
              key: item.key,
              badges: item.badges,
              name: file.name,
              type: ResourceType.file,
              description: '',
            };

            return (
              <FileListItem
                file={fileResource}
                logging={logging}
                key={`lineage-item::${index}`}
                fileHighlights={getHighlightedFileMetadata(fileResource)}
                disabled={false}
              />
            );
          }
        })}
      </div>
      {message && <LineageListMessage message={message} />}
    </>
  );
};

export default LineageList;
