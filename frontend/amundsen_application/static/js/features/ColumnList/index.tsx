// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as ReactMarkdown from 'react-markdown';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import Table, {
  TableColumn as ReusableTableColumn,
  TextAlignmentValues,
} from 'components/Table';
import {
  getMaxNestedColumns,
  getIconNotRequiredStatTypes,
  getTableSortCriterias,
} from 'config/config-utils';

import BadgeList from 'features/BadgeList';

import {
  TableColumn,
  SortCriteria,
  SortDirection,
  IconSizes,
  TypeMetadata,
} from 'interfaces';
import { FormattedDataType, ContentType } from 'interfaces/ColumnList';
import { logAction } from 'utils/analytics';
import { buildTableKey, TablePageParams } from 'utils/navigation';

import { GraphIcon } from 'components/SVGIcons/GraphIcon';

import ColumnType from './ColumnType';
import {
  BLOCKQUOTE_MARKDOWN_TYPE,
  EMPTY_MESSAGE,
  HAS_COLUMN_STATS_TEXT,
  LIST_MARKDOWN_TYPE,
} from './constants';

import './styles.scss';

export interface ComponentProps {
  columns: TableColumn[];
  database: string;
  editText?: string;
  editUrl?: string;
  preExpandPanelKey?: string;
  sortBy?: SortCriteria;
  tableParams: TablePageParams;
  preExpandRightPanel: (columnDetails: FormattedDataType) => void;
  toggleRightPanel: (newColumnDetails: FormattedDataType | undefined) => void;
  hideSomeColumnMetadata: boolean;
  currentSelectedKey: string;
  areNestedColumnsExpanded: boolean | undefined;
  toggleExpandingColumns: () => void;
  hasColumnsToExpand: () => boolean;
}

export type ColumnListProps = ComponentProps;

// TODO: Move this into the configuration once we have more info about the rest of stats
const USAGE_STAT_TYPE = 'column_usage';
const SHOW_STATS_THRESHOLD = 1;
const DEFAULT_SORTING: SortCriteria = {
  name: 'Table Default',
  key: 'sort_order',
  direction: SortDirection.ascending,
};

const getSortingFunction = (
  formattedData: FormattedDataType[],
  sortBy: SortCriteria
) => {
  const numberSortingFunction = (a, b) => b[sortBy.key] - a[sortBy.key];

  const stringSortingFunction = (a, b) => {
    if (a[sortBy.key] && b[sortBy.key]) {
      return a[sortBy.key].localeCompare(b[sortBy.key]);
    }

    return null;
  };

  if (!formattedData.length) {
    return numberSortingFunction;
  }

  return Number.isInteger(formattedData[0][sortBy.key])
    ? numberSortingFunction
    : stringSortingFunction;
};

const hasTypeMetadataWithBadge = (typeMetadata: TypeMetadata[]) => {
  try {
    if (!typeMetadata || !Array.isArray(typeMetadata)) {
      return false;
    }

    return typeMetadata
      .filter((tm) => tm !== null && tm !== undefined)
      .some((tm) => {
        try {
          if (tm.badges?.length) {
            return true;
          }

          const children = (tm.children || []).filter((child) => child !== null && child !== undefined);
          return hasTypeMetadataWithBadge(children);
        } catch (e) {
          return false;
        }
      });
  } catch (e) {
    return false;
  }
};

const hasColumnWithBadge = (columns: TableColumn[]) => {
  if (!columns || !Array.isArray(columns)) {
    return false;
  }

  return columns.some((col) => {
    if (col.badges?.length) {
      return true;
    }

    try {
      const children = col.type_metadata?.children || [];
      return (
        col.type_metadata?.badges?.length ||
        hasTypeMetadataWithBadge(Array.isArray(children) ? children : [])
      );
    } catch (e) {
      return false;
    }
  });
};

const getUsageStat = (item) => {
  const hasItemStats = !!item.stats.length;

  if (hasItemStats) {
    const usageStat = item.stats.find((s) => s.stat_type === USAGE_STAT_TYPE);

    return usageStat ? +usageStat.stat_val : null;
  }

  return null;
};

const hasStatsToDisplayIcon = (stats) => {
  let hasStatsToDisplayIcon = !!stats.length;

  const statTypesToExclude = getIconNotRequiredStatTypes();

  if (hasStatsToDisplayIcon && statTypesToExclude) {
    const allStatTypes = stats.map((stat) => stat.stat_type);
    const statsToInclude = allStatTypes.filter(
      (type) => !statTypesToExclude.includes(type)
    );

    hasStatsToDisplayIcon = !!statsToInclude.length;
  }

  return hasStatsToDisplayIcon;
};

const getColumnMetadataIconElement = (key, popoverText, iconElement) => (
  <OverlayTrigger
    key={key}
    trigger={['hover', 'focus']}
    placement="top"
    overlay={<Popover id="popover-trigger-hover-focus">{popoverText}</Popover>}
  >
    <span>{iconElement}</span>
  </OverlayTrigger>
);

const ColumnList: React.FC<ColumnListProps> = ({
  columns,
  database,
  editText,
  editUrl,
  preExpandPanelKey,
  sortBy = DEFAULT_SORTING,
  tableParams,
  preExpandRightPanel,
  toggleRightPanel,
  hideSomeColumnMetadata,
  currentSelectedKey,
  areNestedColumnsExpanded,
  toggleExpandingColumns,
  hasColumnsToExpand,
}: ColumnListProps) => {
  // STEP 1: Log raw data received from props/API
  // eslint-disable-next-line no-console
  console.log('🟢 ColumnList: STEP 1 - Raw data received', {
    columnsLength: columns?.length,
    columns,
    columnsType: typeof columns,
    isArray: Array.isArray(columns),
    hasNullColumns: columns?.some((c) => c === null || c === undefined),
    columnsDetails: columns?.map((col, idx) => {
      // Defensive check: ensure col is not null before accessing properties
      if (!col || col === null || col === undefined) {
        return {
          index: idx,
          key: null,
          name: null,
          col_type: null,
          type_metadata: null,
          children: [],
          hasTypeMetadata: false,
          typeMetadataChildren: null,
          typeMetadataChildrenLength: 0,
          hasNullChildren: false,
          hasNullTypeMetadataChildren: false,
        };
      }

      // Defensive check: ensure type_metadata is not null before accessing children
      const typeMetadata = (col as any)?.type_metadata;
      const typeMetadataChildren = typeMetadata && typeMetadata !== null && typeof typeMetadata === 'object' && 'children' in typeMetadata ? typeMetadata.children : null;

      return {
        index: idx,
        key: col?.key,
        name: col?.name,
        col_type: col?.col_type,
        type_metadata: typeMetadata,
        children: (col as any)?.children || [],
        hasTypeMetadata: !!typeMetadata,
        typeMetadataChildren: typeMetadataChildren,
        typeMetadataChildrenLength: Array.isArray(typeMetadataChildren) ? typeMetadataChildren.length : 0,
        hasNullChildren: Array.isArray((col as any)?.children) ? ((col as any).children || []).some((c) => c === null || c === undefined) : false,
        hasNullTypeMetadataChildren: Array.isArray(typeMetadataChildren) ? typeMetadataChildren.some((c) => c === null || c === undefined) : false,
      };
    }),
  });

  const hasColumnBadges = hasColumnWithBadge(columns);

  const formatColumnData = (item, index) => {
    // STEP 2: Log each item being formatted
    // eslint-disable-next-line no-console
    console.log(`🟡 ColumnList: STEP 2 - Formatting column ${index}`, {
      index,
      item,
      itemKey: item?.key,
      itemName: item?.name,
      itemColType: item?.col_type,
      itemTypeMetadata: item?.type_metadata,
      itemChildren: item?.children,
      itemChildrenLength: Array.isArray(item?.children) ? item.children.length : 'not an array',
      itemTypeMetadataChildren: item?.type_metadata?.children,
      itemTypeMetadataChildrenLength: Array.isArray(item?.type_metadata?.children) ? item.type_metadata.children.length : 'not an array',
    });
    const hasItemStats = !!item.stats.length;

    return {
      stats: hasItemStats ? item.stats : null,
      content: {
        title: item.name,
        description: item.description,
        hasStats: hasStatsToDisplayIcon(item.stats),
      },
      type: {
        type: item.col_type || '',
        name: item.name || '',
        database: database || '',
      },
      children: (item.children || []).filter((child) => child !== null && child !== undefined),
      sort_order: item.sort_order,
      usage: getUsageStat(item),
      badges: hasColumnBadges ? item.badges : [],
      key: item.key,
      name: item.name,
      isEditable: item.is_editable,
      isExpandable:
        item.type_metadata && item.type_metadata.children && item.type_metadata.children.length > 0,
      editText: editText || null,
      editUrl: editUrl || null,
      tableParams,
      index,
      typeMetadata: item.type_metadata ? {
        ...item.type_metadata,
        children: (item.type_metadata.children || []).filter((child) => child !== null && child !== undefined)
      } : undefined,
      programmaticDescriptions: item.programmatic_descriptions
    };
  };
  // STEP 3: Filter and format data
  const filteredColumns = columns.filter((item) => {
    const isValid = item !== null && item !== undefined;
    if (!isValid) {
      // eslint-disable-next-line no-console
      console.error('🟠 ColumnList: STEP 3 - Filtered out null/undefined column', { item });
    }
    return isValid;
  });

  // eslint-disable-next-line no-console
  console.log('🟢 ColumnList: STEP 3 - After filtering', {
    originalLength: columns.length,
    filteredLength: filteredColumns.length,
    filteredOut: columns.length - filteredColumns.length,
  });

  const formattedData: FormattedDataType[] = filteredColumns.map((item, idx) => {
    const formatted = formatColumnData(item, idx);
    // STEP 4: Log each formatted result
    // eslint-disable-next-line no-console
    console.log(`🟡 ColumnList: STEP 4 - Formatted column ${idx} result`, {
      index: idx,
      originalKey: item?.key,
      formatted,
      formattedType: formatted?.type,
      formattedTypeType: formatted?.type?.type,
      formattedHasType: 'type' in (formatted || {}),
      formattedTypeIsNull: formatted?.type === null,
      formattedTypeIsUndefined: formatted?.type === undefined,
      formattedTypeTypeIsNull: formatted?.type?.type === null,
      formattedTypeTypeIsUndefined: formatted?.type?.type === undefined,
    });
    return formatted;
  });

  // STEP 5: Log formatted data summary
  // eslint-disable-next-line no-console
  console.log('🟢 ColumnList: STEP 5 - Formatted data summary', {
    formattedDataLength: formattedData.length,
    formattedDataWithNullType: formattedData.filter((item) => !item.type || item.type === null),
    formattedDataDetails: formattedData.map((item, idx) => ({
      index: idx,
      key: item?.key,
      name: item?.name,
      hasType: 'type' in (item || {}),
      type: item?.type,
      typeType: item?.type?.type,
      typeIsNull: item?.type === null,
      typeIsUndefined: item?.type === undefined,
      typeTypeIsNull: item?.type?.type === null,
      typeTypeIsUndefined: item?.type?.type === undefined,
    })),
  });

  // Debug logging: identify any rows with a null/invalid `type` field that could cause runtime errors
  try {
    const rowsWithBadType = formattedData.filter(
      (row) => !row || !row.type || row.type === null || row.type.type === null || row.type.type === undefined
    );
    if (rowsWithBadType.length) {
      // eslint-disable-next-line no-console
      console.error('ColumnList detected rows with invalid `type` field', {
        count: rowsWithBadType.length,
        rowsWithBadType: rowsWithBadType.map((row) => ({
          key: row?.key,
          name: row?.name,
          type: row?.type,
          typeMetadata: row?.typeMetadata,
          col_type: row?.type?.type,
          fullRow: row,
        })),
      });
    }

    // Also check for null items in typeMetadata.children arrays
    formattedData.forEach((row, idx) => {
      if (row?.typeMetadata?.children) {
        const nullChildren = row.typeMetadata.children.filter((child) => child === null || child === undefined);
        if (nullChildren.length > 0) {
          // eslint-disable-next-line no-console
          console.error('ColumnList detected null children in typeMetadata', {
            rowIndex: idx,
            rowKey: row.key,
            rowName: row.name,
            typeMetadata: row.typeMetadata,
            nullChildrenCount: nullChildren.length,
            fullRow: row,
          });
        }
      }
    });
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('Error while inspecting formattedData for bad type fields', e);
  }
  const statsCount = formattedData.filter((item) => !!item.stats).length;
  const hasUsageStat =
    getTableSortCriterias().usage && statsCount >= SHOW_STATS_THRESHOLD;

  // STEP 6: Sort data
  let orderedData = formattedData.sort(
    getSortingFunction(formattedData, sortBy)
  );

  if (sortBy.direction === SortDirection.ascending) {
    orderedData = orderedData.reverse();
  }

  // eslint-disable-next-line no-console
  console.log('🟢 ColumnList: STEP 6 - After sorting', {
    orderedDataLength: orderedData.length,
    sortBy,
    orderedDataWithNullType: orderedData.filter((item) => !item.type || item.type === null),
  });

  let tableKey;

  if (orderedData.length) {
    tableKey = buildTableKey(orderedData[0].tableParams);
  }

  let formattedColumns: ReusableTableColumn[] = [
    {
      title: 'Name',
      field: 'content',
      component: (
        { title, description, hasStats }: ContentType,
        index,
        columnDetails: FormattedDataType
      ) => {
        let columnMetadataIcons: React.ReactNode[] = [];

        if (hasStats) {
          const hasStatsIcon = getColumnMetadataIconElement(
            'has-stats',
            HAS_COLUMN_STATS_TEXT,
            <GraphIcon size={IconSizes.SMALL} />
          );

          columnMetadataIcons = [...columnMetadataIcons, hasStatsIcon];
        }

        const handleColumnNameClick = () => {
          toggleRightPanel(columnDetails);
        };

        return (
          <>
            <div className="column-name-container">
              <div className="column-name-with-icons">
                <button
                  className="column-name-button"
                  type="button"
                  onClick={handleColumnNameClick}
                >
                  <h3 className="column-name">{title}</h3>
                </button>
                {columnMetadataIcons}
              </div>
              <ReactMarkdown
                className="column-desc"
                disallowedTypes={[BLOCKQUOTE_MARKDOWN_TYPE, LIST_MARKDOWN_TYPE]}
                unwrapDisallowed
              >
                {description}
              </ReactMarkdown>
            </div>
          </>
        );
      },
    },
    {
      title: 'Type',
      field: 'type',
      component: (type, index, rowData) => {
        // EXTREME LOGGING: Log EVERYTHING about this call
        // eslint-disable-next-line no-console
        console.log('🔴🔴🔴 ColumnList Type column renderer called - EXTREME LOGGING', {
          timestamp: new Date().toISOString(),
          callStack: new Error().stack,
          type,
          typeType: typeof type,
          typeIsNull: type === null,
          typeIsUndefined: type === undefined,
          typeValue: type,
          typeKeys: type && typeof type === 'object' ? Object.keys(type) : 'not an object',
          typeEntries: type && typeof type === 'object' ? Object.entries(type).map(([k, v]) => ({
            key: k,
            value: v,
            valueType: typeof v,
            isNull: v === null,
            isUndefined: v === undefined,
          })) : 'not an object',
          typeDotType: type && typeof type === 'object' && 'type' in type ? (type as any).type : 'NO TYPE PROPERTY',
          typeDotTypeType: type && typeof type === 'object' && 'type' in type ? typeof (type as any).type : 'NO TYPE PROPERTY',
          typeDotTypeIsNull: type && typeof type === 'object' && 'type' in type ? (type as any).type === null : 'NO TYPE PROPERTY',
          typeDotTypeIsUndefined: type && typeof type === 'object' && 'type' in type ? (type as any).type === undefined : 'NO TYPE PROPERTY',
          index,
          rowKey: rowData?.key,
          rowName: rowData?.name,
          rowDataType: typeof rowData,
          rowDataIsNull: rowData === null,
          rowDataIsUndefined: rowData === undefined,
          rowDataKeys: rowData && typeof rowData === 'object' ? Object.keys(rowData) : 'not an object',
          rowDataEntries: rowData && typeof rowData === 'object' ? Object.entries(rowData).map(([k, v]) => ({
            key: k,
            value: v,
            valueType: typeof v,
            isNull: v === null,
            isUndefined: v === undefined,
            isObject: typeof v === 'object' && v !== null,
            objectKeys: (typeof v === 'object' && v !== null) ? Object.keys(v) : [],
          })) : 'not an object',
          fullRowData: rowData,
          fullRowDataStringified: JSON.stringify(rowData),
        });

        // EXTREME LOGGING: Check type before accessing
        // eslint-disable-next-line no-console
        console.log('🔴🔴🔴 ColumnList Type column renderer - BEFORE NULL CHECK', {
          type,
          typeType: typeof type,
          typeIsNull: type === null,
          typeIsUndefined: type === undefined,
          willAccessTypeDotType: type && typeof type === 'object' && 'type' in type,
        });

        if (!type || type === null) {
          // eslint-disable-next-line no-console
          console.error('🔴🔴🔴 ColumnList Type render received null type - RETURNING EARLY', {
            type,
            typeType: typeof type,
            index,
            rowKey: rowData?.key,
            rowName: rowData?.name,
            fullRowData: rowData,
            callStack: new Error().stack,
          });
          return <div className="resource-type">-</div>;
        }

        // EXTREME LOGGING: Check type.type before accessing
        // eslint-disable-next-line no-console
        console.log('🔴🔴🔴 ColumnList Type column renderer - CHECKING type.type', {
          type,
          typeType: typeof type,
          hasTypeProperty: type && typeof type === 'object' && 'type' in type,
          typeDotType: type && typeof type === 'object' && 'type' in type ? (type as any).type : 'NO TYPE PROPERTY',
          typeDotTypeType: type && typeof type === 'object' && 'type' in type ? typeof (type as any).type : 'NO TYPE PROPERTY',
          typeDotTypeIsNull: type && typeof type === 'object' && 'type' in type ? (type as any).type === null : 'NO TYPE PROPERTY',
          typeDotTypeIsUndefined: type && typeof type === 'object' && 'type' in type ? (type as any).type === undefined : 'NO TYPE PROPERTY',
        });

        if (type.type === null || type.type === undefined) {
          // eslint-disable-next-line no-console
          console.error('🔴🔴🔴 ColumnList Type render received type with null type.type', {
            type,
            typeType: type.type,
            typeTypeType: typeof type.type,
            index,
            rowKey: rowData?.key,
            rowName: rowData?.name,
            fullRowData: rowData,
            callStack: new Error().stack,
          });
        }

        // EXTREME LOGGING: Before accessing type.type in JSX
        // eslint-disable-next-line no-console
        console.log('🔴🔴🔴 ColumnList Type column renderer - BEFORE RENDERING ColumnType', {
          type,
          typeDotType: type && typeof type === 'object' && 'type' in type ? (type as any).type : 'NO TYPE PROPERTY',
          typeDotDatabase: type && typeof type === 'object' && 'database' in type ? (type as any).database : 'NO DATABASE PROPERTY',
          typeDotName: type && typeof type === 'object' && 'name' in type ? (type as any).name : 'NO NAME PROPERTY',
          willPassType: type && typeof type === 'object' && 'type' in type ? (type as any).type || '' : '',
          willPassDatabase: type && typeof type === 'object' && 'database' in type ? (type as any).database || '' : '',
          willPassColumnName: type && typeof type === 'object' && 'name' in type ? (type as any).name || '' : '',
        });

        return (
          <div className="resource-type">
            <ColumnType
              type={type.type || ''}
              database={type.database || ''}
              columnName={type.name || ''}
            />
          </div>
        );
      },
    },
  ];

  if (hasUsageStat && !hideSomeColumnMetadata) {
    formattedColumns = [
      ...formattedColumns,
      {
        title: 'Usage',
        field: 'usage',
        horAlign: TextAlignmentValues.right,
        component: (usage) => (
          <p className="resource-type usage-value">{usage}</p>
        ),
      },
    ];
  }

  if (hasColumnBadges && !hideSomeColumnMetadata) {
    formattedColumns = [
      ...formattedColumns,
      {
        title: 'Badges',
        field: 'badges',
        horAlign: TextAlignmentValues.left,
        component: (values) => <BadgeList badges={values} />,
      },
    ];
  }

  const openedColumnsMap = {};
  const handleRowExpand = (rowValues) => {
    if (openedColumnsMap[rowValues.key]) {
      return;
    }
    openedColumnsMap[rowValues.key] = true;
    logAction({
      command: 'click',
      label: `${rowValues.key} ${rowValues.type?.type || ''}`,
      target_id: `column::${rowValues.key}`,
      target_type: 'expand nested columns',
    });
  };

  // Wrapper to ensure formatNestedColumnData never returns null and always has a valid type
  const formatNestedColumnData = (item, index) => {
    try {
      if (!item || item === null) {
        // eslint-disable-next-line no-console
        console.error('formatNestedColumnData received null item', { item, index });
        // Return a safe default object instead of null
        return {
          stats: null,
          content: { title: '', description: '', hasStats: false },
          type: { type: '', name: '', database: database || '' },
          children: [],
          sort_order: 0,
          usage: null,
          badges: [],
          key: `null-item-${index}`,
          name: '',
          isEditable: false,
          isExpandable: false,
          editText: null,
          editUrl: null,
          tableParams,
          index,
          isNestedColumn: true,
          kind: null,
        };
      }

      // Ensure data_type exists, default to empty string if missing
      const dataType = item.data_type || '';
      const itemName = item.name || '';
      const itemKey = item.key || `nested-${index}`;
      const filteredChildren = (item.children || []).filter((child) => child !== null && child !== undefined);

      return {
        stats: null,
        content: {
          title: itemName,
          description: item.description || '',
          hasStats: false,
        },
        type: {
          type: dataType,
          name: itemName,
          database: database || '',
        },
        children: filteredChildren,
        sort_order: item.sort_order || 0,
        usage: null,
        badges: item.badges || [],
        key: itemKey,
        name: itemName,
        isEditable: item.is_editable || false,
        isExpandable: filteredChildren.length > 0,
        editText: editText || null,
        editUrl: editUrl || null,
        tableParams,
        index,
        isNestedColumn: true,
        kind: item.kind || null,
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('formatNestedColumnData error', { error, item, index });
      // Return a safe default object on any error
      return {
        stats: null,
        content: { title: '', description: '', hasStats: false },
        type: { type: '', name: '', database: database || '' },
        children: [],
        sort_order: 0,
        usage: null,
        badges: [],
        key: `error-item-${index}`,
        name: '',
        isEditable: false,
        isExpandable: false,
        editText: null,
        editUrl: null,
        tableParams,
        index,
        isNestedColumn: true,
        kind: null,
      };
    }
  };

  // STEP 7: Final sanitization: ensure all data items have valid type objects
  // eslint-disable-next-line no-console
  console.log('🟢 ColumnList: STEP 7 - Starting sanitization', {
    orderedDataLength: orderedData.length,
  });

  const sanitizedData = orderedData.map((item, idx) => {
    if (!item || item === null) {
      // eslint-disable-next-line no-console
      console.error('🔴 ColumnList sanitizedData: NULL ITEM DETECTED', {
        idx,
        item,
        orderedDataLength: orderedData.length,
        orderedDataIndices: orderedData.map((d, i) => ({
          index: i,
          key: d?.key,
          name: d?.name,
          hasType: 'type' in (d || {}),
          typeIsNull: d?.type === null,
        })),
      });
      return null;
    }

    // Ensure type object exists and is valid
    if (!item.type || item.type === null) {
      // eslint-disable-next-line no-console
      console.error('🔴 ColumnList sanitizedData: ITEM HAS NULL TYPE FIELD', {
        idx,
        itemKey: item.key,
        itemName: item.name,
        itemType: item.type,
        itemTypeType: item.type && typeof item.type === 'object' && 'type' in item.type ? (item.type as any).type : undefined,
        itemHasTypeProperty: 'type' in item,
        fullItem: JSON.parse(JSON.stringify(item)), // Deep clone
        itemKeys: Object.keys(item),
        itemEntries: Object.entries(item).map(([k, v]) => ({
          key: k,
          value: v,
          valueType: typeof v,
          isNull: v === null,
          isUndefined: v === undefined,
        })),
        orderedDataLength: orderedData.length,
      });
      return {
        ...item,
        type: {
          type: (item.type && typeof item.type === 'object' && 'type' in item.type ? (item.type as any).type : '') || '',
          name: (item.type && typeof item.type === 'object' && 'name' in item.type ? (item.type as any).name : item.name) || '',
          database: (item.type && typeof item.type === 'object' && 'database' in item.type ? (item.type as any).database : database) || '',
        },
      };
    }

    // Check if type.type is null (the nested property)
    if (item.type && typeof item.type === 'object' && 'type' in item.type && ((item.type as any).type === null || (item.type as any).type === undefined)) {
      // eslint-disable-next-line no-console
      console.error('🔴 ColumnList sanitizedData: TYPE OBJECT HAS NULL .type PROPERTY', {
        idx,
        itemKey: item.key,
        itemName: item.name,
        typeObject: item.type,
        typeObjectType: item.type && typeof item.type === 'object' && 'type' in item.type ? (item.type as any).type : undefined,
        typeObjectKeys: Object.keys(item.type || {}),
        typeObjectEntries: Object.entries(item.type || {}).map(([k, v]) => ({
          key: k,
          value: v,
          valueType: typeof v,
          isNull: v === null,
        })),
        fullItem: JSON.parse(JSON.stringify(item)),
      });
      return {
        ...item,
        type: {
          type: (item.type && typeof item.type === 'object' && 'type' in item.type ? (item.type as any).type : '') || '',
          name: (item.type && typeof item.type === 'object' && 'name' in item.type ? (item.type as any).name : item.name) || '',
          database: (item.type && typeof item.type === 'object' && 'database' in item.type ? (item.type as any).database : database) || '',
        },
      };
    }

    return item;
  }).filter((item): item is FormattedDataType => item !== null && item !== undefined);

  // STEP 8: Log final sanitized data before passing to Table - EXTREME LOGGING
  // eslint-disable-next-line no-console
  console.log('🔴🔴🔴 ColumnList: STEP 8 - Final sanitized data ready for Table - EXTREME LOGGING', {
    timestamp: new Date().toISOString(),
    sanitizedDataLength: sanitizedData.length,
    sanitizedData: sanitizedData,
    sanitizedDataStringified: JSON.stringify(sanitizedData),
    sanitizedDataWithNullType: sanitizedData.filter((item) => !item.type || item.type === null),
    sanitizedDataDetails: sanitizedData.map((item, idx) => ({
      index: idx,
      item: item,
      itemStringified: JSON.stringify(item),
      key: item?.key,
      name: item?.name,
      hasType: item && typeof item === 'object' && 'type' in item,
      type: item && typeof item === 'object' && 'type' in item ? (item as any).type : 'NO TYPE PROPERTY',
      typeStringified: item && typeof item === 'object' && 'type' in item ? JSON.stringify((item as any).type) : 'NO TYPE PROPERTY',
      typeTypeValue: typeof (item && typeof item === 'object' && 'type' in item ? (item as any).type : undefined),
      typeIsNull: item && typeof item === 'object' && 'type' in item ? (item as any).type === null : 'NO TYPE PROPERTY',
      typeIsUndefined: item && typeof item === 'object' && 'type' in item ? (item as any).type === undefined : 'NO TYPE PROPERTY',
      typeKeys: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null ? Object.keys((item as any).type) : 'NO TYPE PROPERTY OR NOT OBJECT',
      typeEntries: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null ? Object.entries((item as any).type).map(([k, v]) => ({
        key: k,
        value: v,
        valueType: typeof v,
        isNull: v === null,
        isUndefined: v === undefined,
      })) : 'NO TYPE PROPERTY OR NOT OBJECT',
      typeDotType: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type : 'NO TYPE.TYPE PROPERTY',
      typeTypeType: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? typeof ((item as any).type as any).type : 'NO TYPE.TYPE PROPERTY',
      typeTypeIsNull: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type === null : 'NO TYPE.TYPE PROPERTY',
      typeTypeIsUndefined: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type === undefined : 'NO TYPE.TYPE PROPERTY',
    })),
    formattedColumnsLength: formattedColumns.length,
    formattedColumns: formattedColumns,
    formattedColumnsStringified: JSON.stringify(formattedColumns),
    callStack: new Error().stack,
  });

  // STEP 9: Pass data to Table component - EXTREME LOGGING
  // eslint-disable-next-line no-console
  console.log('🔴🔴🔴 ColumnList: STEP 9 - Passing data to Table component - EXTREME LOGGING', {
    timestamp: new Date().toISOString(),
    dataLength: sanitizedData.length,
    data: sanitizedData,
    dataStringified: JSON.stringify(sanitizedData),
    dataDetails: sanitizedData.map((item, idx) => ({
      index: idx,
      item: item,
      itemStringified: JSON.stringify(item),
      hasType: item && typeof item === 'object' && 'type' in item,
      type: item && typeof item === 'object' && 'type' in item ? (item as any).type : 'NO TYPE PROPERTY',
      typeStringified: item && typeof item === 'object' && 'type' in item ? JSON.stringify((item as any).type) : 'NO TYPE PROPERTY',
    })),
    columnsLength: formattedColumns.length,
    columns: formattedColumns,
    columnsStringified: JSON.stringify(formattedColumns),
    callStack: new Error().stack,
  });

  return (
    <Table
      columns={formattedColumns}
      data={sanitizedData}
      options={{
        rowHeight: 72,
        emptyMessage: EMPTY_MESSAGE,
        formatChildrenData: formatNestedColumnData,
        onExpand: handleRowExpand,
        onRowClick: toggleRightPanel,
        tableClassName: 'table-detail-table',
        preExpandRightPanel,
        preExpandPanelKey,
        currentSelectedKey,
        tableKey,
        maxNumRows: getMaxNestedColumns(),
        shouldExpandAllRows: areNestedColumnsExpanded,
        toggleExpandingRows: toggleExpandingColumns,
        hasRowsToExpand: hasColumnsToExpand,
      }}
    />
  );
};

export default ColumnList;
