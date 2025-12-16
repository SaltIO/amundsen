// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { FormattedDataType } from 'interfaces/ColumnList';
import { IconSizes } from 'interfaces/Enums';

import ShimmeringResourceLoader from '../ShimmeringResourceLoader';
import { RightTriangleIcon, DownTriangleIcon } from '../SVGIcons';

import {
  ARRAY_KIND,
  ARRAY_LABEL,
  ARRAY_OPENER,
  ARRAY_CLOSER,
  COLUMN_NAME_REGEX,
  MAP_KIND,
  MAP_LABEL,
  MAP_OPENER,
  MAP_CLOSER,
  TYPE_METADATA_REGEX,
  MAP_KEY_NAME,
  MAP_VALUE_NAME,
  MAP_KEY_DISPLAY_NAME,
  MAP_VALUE_DISPLAY_NAME,
  SCROLL_INTO_VIEW_BLOCK,
} from './constants';
import './styles.scss';

export enum TextAlignmentValues {
  left = 'left',
  right = 'right',
  center = 'center',
}
export interface TableColumn {
  title: string;
  field: string;
  horAlign?: TextAlignmentValues;
  component?: (
    value: any,
    index: number,
    columnDetails: ValidData
  ) => React.ReactNode;
  width?: number;
  // sortable?: bool (false)
}

type Some = string | number | boolean | symbol | bigint | object;
type ValidData = Record<string, Some | null>; // Removes the undefined values

interface RowData {
  [key: string]: Some | null;
}

export interface TableOptions {
  /** Optional additional class name to identify the table */
  tableClassName?: string;
  /** Whether if the table contents are being loaded, shows a skeleton/shimmer loader if true */
  isLoading?: boolean;
  /** When isLoading is true, this number specifies the count of loading blocks that we will show */
  numLoadingBlocks?: number;
  /** Height of all regular (not expanded) rows */
  rowHeight?: number;
  /** Row key that is set when user navigates to a specific column link used to pre expand the details panel */
  preExpandPanelKey?: string;
  /** Callback when a row is expanded */
  onExpand?: (rowValues: any, key: string) => void;
  /** Callback when a row is collapsed */
  onCollapse?: (rowValues: any, key: string) => void;
  /** Callback when a row is clicked */
  onRowClick?: (rowValues: any, index: string) => void;
  /** Optional empty table message to be shown */
  emptyMessage?: string;
  /** Row key of the currently seleected row */
  currentSelectedKey?: string;
  /** Key corresponding to the dataset table currently being viewed */
  tableKey?: string;
  /** Function used to format the data displayed in the expanded child rows */
  formatChildrenData?: (item: any, index: number) => FormattedDataType | null;
  /** Function used to pre expand the right panel with the designated details */
  preExpandRightPanel?: (columnDetails: FormattedDataType) => void;
  /** Expand all child rows by default if the total number of rows does not exceed this value */
  maxNumRows?: number;
  /** Specifies if all the child rows should be expanded if true */
  shouldExpandAllRows?: boolean;
  /** Toggles to expand or collapse all rows */
  toggleExpandingRows?: () => void;
  /** Specifies whether one or more rows are expandable */
  hasRowsToExpand?: () => boolean;
}

export interface TableProps {
  data: RowData[];
  columns: TableColumn[];
  options?: TableOptions;
}

export interface TableRowProps {
  columnKey: string;
  currentSelectedKey?: string;
  columns: TableColumn[];
  rowValues: ValidData;
  rowStyles: { height: string };
  onExpand?: (rowValues: any, key: string) => void;
  onCollapse?: (rowValues: any, key: string) => void;
  onRowClick?: (rowValues: any, key: string) => void;
  expandRowRef?: React.RefObject<HTMLTableRowElement>;
  expandedRows: RowKey[];
  setExpandedRows: (key) => void;
  nestedLevel: number;
}

type RowStyles = {
  height: string;
};

type EmptyRowProps = {
  colspan: number;
  rowStyles: RowStyles;
  emptyMessage?: string;
};

type TableRowDetails = {
  data: ValidData[];
  columns: TableColumn[];
  currentSelectedKey?: string;
  preExpandPanelKey?: string;
  rowStyles: { height: string };
  onExpand?: (rowValues: any, key: string) => void;
  onCollapse?: (rowValues: any, key: string) => void;
  onRowClick?: (rowValues: any, key: string) => void;
  expandRowRef?: React.RefObject<HTMLTableRowElement>;
  expandedRows: RowKey[];
  setExpandedRows: (keys: string[]) => void;
  formatChildrenData?: (item: any, index: number) => FormattedDataType | null;
  preExpandRightPanel?: (columnDetails: FormattedDataType) => void;
  nestedLevel: number;
};

type ExpandCollapseAllRowsInput = {
  allColumnKeys: string[];
  shouldExpandAllRows: boolean | undefined;
  setExpandedRows: (keys: string[]) => void;
  initialExpandedRows: string[];
  maxNumRows: number | undefined;
  toggleExpandingRows: (() => void) | undefined;
};

type TableHooksInput = {
  data: ValidData[];
  maxNumRows: number | undefined;
  preExpandPanelKey: string | undefined;
  tableKey: string | undefined;
  shouldExpandAllRows: boolean | undefined;
  toggleExpandingRows: (() => void) | undefined;
};

const DEFAULT_EMPTY_MESSAGE = 'No Results';
const EXPAND_ROW_TEXT = 'Expand Row';
const INVALID_DATA_ERROR_MESSAGE =
  'Invalid data! Your data does not contain the fields specified on the columns property.';
const DEFAULT_LOADING_ITEMS = 3;
const DEFAULT_ROW_HEIGHT = 30;
const EXPANDING_BUTTON_WIDTH = 60;
const NESTED_EXPANDING_BUTTON_WIDTH = 40;
const FIRST_LEVEL_INDENTATION_WIDTH = 50;
const INDENTATION_WIDTH = 25;
const DEFAULT_TEXT_ALIGNMENT = TextAlignmentValues.left;
const DEFAULT_CELL_WIDTH = 'auto';
const ALIGNEMENT_TO_CLASS_MAP = {
  left: 'is-left-aligned',
  right: 'is-right-aligned',
  center: 'is-center-aligned',
};

const getCellAlignmentClass = (alignment: TextAlignmentValues) =>
  ALIGNEMENT_TO_CLASS_MAP[alignment];

const getExpandingButtonWidth = (nestedLevel) =>
  nestedLevel === 0 ? EXPANDING_BUTTON_WIDTH : NESTED_EXPANDING_BUTTON_WIDTH;

const getIndentationPaddingSize = (nestedLevel, isExpandable) => {
  let indentationLevelPadding = 0;

  if (nestedLevel > 0) {
    indentationLevelPadding =
      FIRST_LEVEL_INDENTATION_WIDTH + INDENTATION_WIDTH * (nestedLevel - 1);
  }
  const expandingButtonPlaceholder = !isExpandable
    ? getExpandingButtonWidth(nestedLevel)
    : 0;

  return `${indentationLevelPadding + expandingButtonPlaceholder}px`;
};

const fieldIsDefined = (field, row) => row[field] !== undefined;

const checkIfValidData = (
  data: unknown[],
  fields: string[]
): data is ValidData[] => {
  let isValid = true;

  for (let i = 0; i < fields.length; i++) {
    if (!data.some(fieldIsDefined.bind(null, fields[i]))) {
      isValid = false;
      break;
    }
  }

  return isValid;
};

const updateMapDisplayNames = (childrenData) => {
  if (!childrenData || !Array.isArray(childrenData)) {
    return [];
  }
  return childrenData
    .filter((child) => child !== null && child !== undefined)
    .map((child) => {
      let displayName = child.name;

    if (child.name === MAP_KEY_NAME) {
      displayName = MAP_KEY_DISPLAY_NAME;
    } else if (child.name === MAP_VALUE_NAME) {
      displayName = MAP_VALUE_DISPLAY_NAME;
    }

      return { ...child, content: { ...child.content, title: displayName } };
    });
};

const getAllColumnKeys = (columns) => {
  if (!columns || !Array.isArray(columns)) {
    return [];
  }

  return columns
    .filter((col) => col !== null && col !== undefined)
    .reduce((prevKeys, col: FormattedDataType) => {
      let childKeys = [];

      if (col.typeMetadata?.children?.length) {
        childKeys = getAllColumnKeys(col.typeMetadata.children);
      } else if (col.children?.length) {
        childKeys = getAllColumnKeys(col.children);
      }

      return [...prevKeys, col.key, ...childKeys];
    }, []);
};

const getKeysToExpand = (preExpandPanelKey, tableKey) => {
  // If the key to preexpand is a nested column, need to add each key level to the expanded row list
  let keysToExpand: string[] = [];

  if (preExpandPanelKey) {
    const columnKeyRegex = tableKey + COLUMN_NAME_REGEX;
    const columnKey = preExpandPanelKey.match(columnKeyRegex);

    if (columnKey) {
      keysToExpand = [columnKey[0]];
    }

    let nextKeyRegex = columnKeyRegex + TYPE_METADATA_REGEX;
    let nextKey = preExpandPanelKey.match(nextKeyRegex);

    while (nextKey) {
      keysToExpand = [...keysToExpand, nextKey[0]];
      nextKeyRegex += COLUMN_NAME_REGEX;
      nextKey = preExpandPanelKey.match(nextKeyRegex);
    }
  }

  return keysToExpand;
};

const getInitialExpandedRows = (
  data,
  allColumnKeys,
  maxNumRows,
  preExpandPanelKey,
  tableKey
) =>
  allColumnKeys.length <= maxNumRows
    ? allColumnKeys
    : getKeysToExpand(preExpandPanelKey, tableKey);

const expandOrCollapseAllRows = ({
  allColumnKeys,
  shouldExpandAllRows,
  setExpandedRows,
  initialExpandedRows,
  maxNumRows,
  toggleExpandingRows,
}: ExpandCollapseAllRowsInput) => {
  if (shouldExpandAllRows !== undefined) {
    if (shouldExpandAllRows) {
      setExpandedRows(allColumnKeys);
    } else {
      setExpandedRows([]);
    }
  } else if (maxNumRows && allColumnKeys.length > maxNumRows) {
    // This case is hit when first loading the page and all rows should be collapsed by default
    if (initialExpandedRows.length > 0) {
      // A subset of initial rows to expand has been specified
      setExpandedRows(initialExpandedRows);
    } else if (toggleExpandingRows) {
      // Sets the value to false so the page knows to display the option to expand all rows
      // instead of the default of collapse all
      toggleExpandingRows();
    }
  }
};

const getFormattedChildrenData = (item, formatChildrenData) => {
  // STEP 15: Log when processing children data
  // eslint-disable-next-line no-console
  console.log('🟠 Table: STEP 15 - getFormattedChildrenData called', {
    item,
    itemKey: item?.key,
    itemName: item?.name,
    hasTypeMetadata: !!item?.typeMetadata,
    typeMetadata: item?.typeMetadata,
    hasChildren: !!item?.children,
    children: item?.children,
    childrenLength: Array.isArray(item?.children) ? item.children.length : 'not an array',
  });

  try {
    if (item.typeMetadata) {
      // eslint-disable-next-line no-console
      console.log('🟠 Table: STEP 15a - Processing typeMetadata', {
        typeMetadata: item.typeMetadata,
        typeMetadataType: typeof item.typeMetadata,
      });

      const results = [item.typeMetadata]
        .map((tm, idx) => {
          try {
            // eslint-disable-next-line no-console
            console.log(`🟠 Table: STEP 15b - Formatting typeMetadata item ${idx}`, {
              idx,
              tm,
              tmType: typeof tm,
              tmIsNull: tm === null,
              tmIsUndefined: tm === undefined,
            });
            const result = formatChildrenData(tm, idx);
            // eslint-disable-next-line no-console
            console.log(`🟠 Table: STEP 15c - Formatted typeMetadata item ${idx} result`, {
              idx,
              result,
              resultType: typeof result,
              resultIsNull: result === null,
              resultHasType: result && typeof result === 'object' && 'type' in result,
              resultTypeField: result && typeof result === 'object' && 'type' in result ? (result as any).type : undefined,
            });
            return result;
          } catch (error) {
            // eslint-disable-next-line no-console
            console.error('🔴 getFormattedChildrenData error formatting typeMetadata', {
              error,
              errorMessage: error?.message,
              errorStack: error?.stack,
              tm,
              tmType: typeof tm,
              idx,
            });
            return null;
          }
        })
        .filter((result) => {
          const isValid = result !== null && result !== undefined;
          if (!isValid) {
            // eslint-disable-next-line no-console
            console.error('🔴 getFormattedChildrenData: Filtered out null result', { result });
          }
          return isValid;
        });

      // Ensure all results have valid type objects
      const finalResults = results.map((result, resultIdx) => {
        // eslint-disable-next-line no-console
        console.log(`🟠 Table: STEP 15d - Ensuring valid type for result ${resultIdx}`, {
          resultIdx,
          result,
          resultHasType: result && typeof result === 'object' && 'type' in result,
          resultType: result && typeof result === 'object' && 'type' in result ? (result as any).type : undefined,
          resultTypeIsNull: result && typeof result === 'object' && 'type' in result ? (result as any).type === null : false,
        });

        if (!result || typeof result !== 'object' || !('type' in result) || (result as any).type === null) {
          // eslint-disable-next-line no-console
          console.error('🔴 getFormattedChildrenData: Result has null/invalid type, fixing', {
            resultIdx,
            result,
            resultType: result && typeof result === 'object' && 'type' in result ? (result as any).type : undefined,
          });
          return {
            ...result,
            type: {
              type: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'type' in (result as any).type ? ((result as any).type as any).type : '',
              name: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'name' in (result as any).type ? ((result as any).type as any).name : (result as any)?.name || '',
              database: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'database' in (result as any).type ? ((result as any).type as any).database : '',
            },
          };
        }
        return result;
      });

      // eslint-disable-next-line no-console
      console.log('🟠 Table: STEP 15e - Final results from typeMetadata', {
        finalResultsLength: finalResults.length,
        finalResults,
      });

      return finalResults;
    }

    // eslint-disable-next-line no-console
    console.log('🟠 Table: STEP 15f - Processing children array', {
      itemChildren: item?.children,
      childrenLength: Array.isArray(item?.children) ? item.children.length : 'not an array',
    });

    const children = (item.children || [])
      .filter((child, childIdx) => {
        const isValid = child !== null && child !== undefined;
        if (!isValid) {
          // eslint-disable-next-line no-console
          console.error('🔴 getFormattedChildrenData: Filtered out null child', { childIdx, child });
        }
        return isValid;
      });

    // eslint-disable-next-line no-console
    console.log('🟠 Table: STEP 15g - After filtering children', {
      originalLength: Array.isArray(item?.children) ? item.children.length : 0,
      filteredLength: children.length,
    });

    const results = children
      .map((child, idx) => {
        try {
          // eslint-disable-next-line no-console
          console.log(`🟠 Table: STEP 15h - Formatting child ${idx}`, {
            idx,
            child,
            childType: typeof child,
            childIsNull: child === null,
          });
          const result = formatChildrenData(child, idx);
          // eslint-disable-next-line no-console
          console.log(`🟠 Table: STEP 15i - Formatted child ${idx} result`, {
            idx,
            result,
            resultType: typeof result,
            resultIsNull: result === null,
            resultHasType: result && typeof result === 'object' && 'type' in result,
          });
          return result;
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('🔴 getFormattedChildrenData error formatting child', {
            error,
            errorMessage: error?.message,
            errorStack: error?.stack,
            child,
            childType: typeof child,
            idx,
          });
          return null;
        }
      })
      .filter((result) => {
        const isValid = result !== null && result !== undefined;
        if (!isValid) {
          // eslint-disable-next-line no-console
          console.error('🔴 getFormattedChildrenData: Filtered out null result from children', { result });
        }
        return isValid;
      });

    // Ensure all results have valid type objects
    const finalResults = results.map((result, resultIdx) => {
      // eslint-disable-next-line no-console
      console.log(`🟠 Table: STEP 15j - Ensuring valid type for child result ${resultIdx}`, {
        resultIdx,
        result,
        resultHasType: result && typeof result === 'object' && 'type' in result,
        resultType: result && typeof result === 'object' && 'type' in result ? (result as any).type : undefined,
        resultTypeIsNull: result && typeof result === 'object' && 'type' in result ? (result as any).type === null : false,
      });

      if (!result || typeof result !== 'object' || !('type' in result) || (result as any).type === null) {
        // eslint-disable-next-line no-console
        console.error('🔴 getFormattedChildrenData: Child result has null/invalid type, fixing', {
          resultIdx,
          result,
          resultType: result && typeof result === 'object' && 'type' in result ? (result as any).type : undefined,
        });
        return {
          ...result,
          type: {
            type: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'type' in (result as any).type ? ((result as any).type as any).type : '',
            name: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'name' in (result as any).type ? ((result as any).type as any).name : (result as any)?.name || '',
            database: result && typeof result === 'object' && 'type' in result && typeof (result as any).type === 'object' && (result as any).type !== null && 'database' in (result as any).type ? ((result as any).type as any).database : '',
          },
        };
      }
      return result;
    });

    // eslint-disable-next-line no-console
    console.log('🟠 Table: STEP 15k - Final results from children', {
      finalResultsLength: finalResults.length,
      finalResults,
    });

    return finalResults;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('getFormattedChildrenData error', { error, item });
    return [];
  }
};

const handleSpecificTypeRowData = (initialRowValues, formatChildrenData) => {
  // STEP 16: Log when handling specific type row data
  // eslint-disable-next-line no-console
  console.log('🟠 Table: STEP 16 - handleSpecificTypeRowData called', {
    initialRowValues,
    initialRowValuesKey: initialRowValues?.key,
    initialRowValuesName: initialRowValues?.name,
    hasTypeMetadata: !!initialRowValues?.typeMetadata,
    typeMetadata: initialRowValues?.typeMetadata,
    hasChildren: !!initialRowValues?.children,
    children: initialRowValues?.children,
  });

  // Retrieve the initial formatted child data and row values to be displayed
  let formattedChildren = initialRowValues.typeMetadata
    ? getFormattedChildrenData(initialRowValues, formatChildrenData)
    : [];

  // eslint-disable-next-line no-console
  console.log('🟠 Table: STEP 16a - After getFormattedChildrenData', {
    formattedChildrenLength: formattedChildren.length,
    formattedChildren,
    formattedChildrenWithNullType: formattedChildren.filter((fc) => !fc || typeof fc !== 'object' || !('type' in fc) || (fc as any).type === null),
  });

  let rowValuesToDisplay = initialRowValues.typeMetadata && formattedChildren[0]
    ? formattedChildren[0]
    : initialRowValues;

  // eslint-disable-next-line no-console
  console.log('🟠 Table: STEP 16b - rowValuesToDisplay determined', {
    rowValuesToDisplay,
    rowValuesToDisplayKey: rowValuesToDisplay?.key,
    rowValuesToDisplayName: rowValuesToDisplay?.name,
    rowValuesToDisplayHasType: rowValuesToDisplay && typeof rowValuesToDisplay === 'object' && 'type' in rowValuesToDisplay,
    rowValuesToDisplayType: rowValuesToDisplay && typeof rowValuesToDisplay === 'object' && 'type' in rowValuesToDisplay ? (rowValuesToDisplay as any).type : undefined,
    rowValuesToDisplayTypeIsNull: rowValuesToDisplay && typeof rowValuesToDisplay === 'object' && 'type' in rowValuesToDisplay ? (rowValuesToDisplay as any).type === null : false,
  });

  // Handle array kinds
  let arrayCount = 0;

  while (rowValuesToDisplay && rowValuesToDisplay.kind === ARRAY_KIND) {
    // Keep track of how many nested array levels there are
    arrayCount++;
    formattedChildren = getFormattedChildrenData(
      rowValuesToDisplay,
      formatChildrenData
    );

    // Skip over any array type metadata by moving on to the next child level
    if (formattedChildren[0] && formattedChildren[0].isExpandable) {
      [rowValuesToDisplay] = formattedChildren;
    } else {
      if (formattedChildren[0] && formattedChildren[0].kind === ARRAY_KIND) {
        arrayCount++;
      }
      break;
    }
  }

  if (rowValuesToDisplay.kind === ARRAY_KIND) {
    // The innermost nested kind is array, so don't display an extra row for its terminal state
    formattedChildren = [];
  } else {
    // Get the formatted children for the final rowValuesToDisplay
    formattedChildren = getFormattedChildrenData(
      rowValuesToDisplay,
      formatChildrenData
    );

    if (rowValuesToDisplay.kind === MAP_KIND) {
      formattedChildren = updateMapDisplayNames(formattedChildren);
    }
  }

  return { rowValuesToDisplay, formattedChildren, arrayCount };
};

const getSpecificTypeOpenerRow = (
  rowValuesToDisplay,
  arrayCount,
  nestedLevel,
  additionalTableColCount
) => {
  const hasSpecificTypeHandling =
    arrayCount > 0 || rowValuesToDisplay.kind === MAP_KIND;

  if (!hasSpecificTypeHandling) {
    return null;
  }

  let arrayOpenerLabel = '';

  if (arrayCount > 0) {
    arrayOpenerLabel = ARRAY_LABEL + ARRAY_OPENER.repeat(arrayCount);
  }

  let mapOpenerLabel = '';

  if (rowValuesToDisplay.kind === MAP_KIND) {
    mapOpenerLabel = MAP_LABEL + MAP_OPENER;
  }

  const cellStyle = {
    paddingLeft: getIndentationPaddingSize(nestedLevel, false),
  };

  return (
    <tr
      className="ams-table-row is-nested-column-row is-specific-type-row"
      key={`openerRow:${rowValuesToDisplay.key}`}
    >
      <td key={`openerCell:${rowValuesToDisplay.key}`} style={cellStyle}>
        <span className="column-type-label">
          {arrayOpenerLabel} {mapOpenerLabel}
        </span>
      </td>
      {[...Array(additionalTableColCount)].map((value, index) => (
        <td key={`openerCellPlaceholder${index}:${rowValuesToDisplay.key}`} />
      ))}
    </tr>
  );
};

const getSpecificTypeCloserRow = (
  rowValuesToDisplay,
  arrayCount,
  nestedLevel,
  additionalTableColCount
) => {
  const hasSpecificTypeHandling =
    arrayCount > 0 || rowValuesToDisplay.kind === MAP_KIND;

  if (!hasSpecificTypeHandling) {
    return null;
  }

  let arrayCloserLabel = '';

  if (arrayCount > 0) {
    arrayCloserLabel = ARRAY_CLOSER.repeat(arrayCount);
  }

  let mapCloserLabel = '';

  if (rowValuesToDisplay.kind === MAP_KIND) {
    mapCloserLabel = MAP_CLOSER;
  }

  const cellStyle = {
    paddingLeft: getIndentationPaddingSize(nestedLevel, false),
  };

  return (
    <tr
      className="ams-table-row is-nested-column-row is-specific-type-row"
      key={`closerRow:${rowValuesToDisplay.key}`}
    >
      <td key={`closerCell:${rowValuesToDisplay.key}`} style={cellStyle}>
        <span className="column-type-label">
          {mapCloserLabel} {arrayCloserLabel}
        </span>
      </td>
      {[...Array(additionalTableColCount)].map((value, index) => (
        <td key={`closerCellPlaceholder${index}:${rowValuesToDisplay.key}`} />
      ))}
    </tr>
  );
};

const EmptyRow: React.FC<EmptyRowProps> = ({
  colspan,
  rowStyles,
  emptyMessage = DEFAULT_EMPTY_MESSAGE,
}: EmptyRowProps) => (
  <tr className="ams-table-row is-empty" style={rowStyles}>
    <td className="ams-empty-message-cell" colSpan={colspan}>
      {emptyMessage}
    </td>
  </tr>
);

const ShimmeringHeader: React.FC = () => (
  <tr>
    <th className="ams-table-heading-loading-cell">
      <div className="ams-table-shimmer-block" />
    </th>
  </tr>
);

type ShimmeringBodyProps = {
  numLoadingBlocks: number;
};

const ShimmeringBody: React.FC<ShimmeringBodyProps> = ({
  numLoadingBlocks,
}: ShimmeringBodyProps) => (
  <tr className="ams-table-row">
    <td className="ams-table-body-loading-cell">
      <ShimmeringResourceLoader numItems={numLoadingBlocks} />
    </td>
  </tr>
);

type ExpandCollapseAllButtonProps = {
  shouldExpandAllRows?: boolean;
  hasRowsToExpand?: () => boolean;
  toggleExpandingRows?: () => void;
};
const ExpandCollapseAllButton: React.FC<ExpandCollapseAllButtonProps> = ({
  shouldExpandAllRows,
  hasRowsToExpand,
  toggleExpandingRows,
}: ExpandCollapseAllButtonProps) => {
  const buttonContainerStyle = {
    width: `${getExpandingButtonWidth(0)}px`,
  };

  return (
    <span
      className="ams-table-expanding-button-container"
      style={buttonContainerStyle}
    >
      {hasRowsToExpand && hasRowsToExpand() && (
        <button
          type="button"
          className="btn ams-table-expanding-button is-expand-collapse-all"
          onClick={toggleExpandingRows}
        >
          <span className="sr-only">{EXPAND_ROW_TEXT}</span>
          {shouldExpandAllRows || shouldExpandAllRows === undefined ? (
            <DownTriangleIcon size={IconSizes.SMALL} />
          ) : (
            <RightTriangleIcon size={IconSizes.SMALL} />
          )}
        </button>
      )}
    </span>
  );
};

type ExpandingButtonProps = {
  rowKey: string;
  expandedRows: RowKey[];
  rowValues: any;
  onClick: (index) => void;
  onExpand?: (rowValues: any, key: string) => void;
  onCollapse?: (rowValues: any, key: string) => void;
  nestedLevel: number;
};
const ExpandingButton: React.FC<ExpandingButtonProps> = ({
  rowKey,
  onClick,
  onExpand,
  onCollapse,
  rowValues,
  expandedRows,
  nestedLevel,
}: ExpandingButtonProps) => {
  const isExpanded = expandedRows.includes(rowKey);
  const buttonContainerStyle = {
    width: `${getExpandingButtonWidth(nestedLevel)}px`,
  };

  const handleExpandButton = (event) => {
    event.stopPropagation();

    const newExpandedRows = isExpanded
      ? expandedRows.filter((k) => k !== rowKey)
      : [...expandedRows, rowKey];

    onClick(newExpandedRows);

    if (!isExpanded && onExpand) {
      onExpand(rowValues, rowKey);
    }
    if (isExpanded && onCollapse) {
      onCollapse(rowValues, rowKey);
    }
  };

  return (
    <span
      className="ams-table-expanding-button-container"
      style={buttonContainerStyle}
    >
      <button
        key={rowKey}
        type="button"
        className="btn ams-table-expanding-button"
        onClick={handleExpandButton}
      >
        <span className="sr-only">{EXPAND_ROW_TEXT}</span>
        {isExpanded ? (
          <DownTriangleIcon size={IconSizes.SMALL} />
        ) : (
          <RightTriangleIcon size={IconSizes.SMALL} />
        )}
      </button>
    </span>
  );
};

const TableRow: React.FC<TableRowProps> = ({
  columnKey,
  currentSelectedKey,
  columns,
  rowValues,
  rowStyles,
  onExpand,
  onCollapse,
  onRowClick,
  expandRowRef,
  expandedRows,
  setExpandedRows,
  nestedLevel,
}: TableRowProps) => {
  // STEP 12: Log data received by TableRow component
  // eslint-disable-next-line no-console
  console.log('🟣 TableRow: STEP 12 - Rendering row', {
    columnKey,
    rowValues,
    rowValuesType: typeof rowValues,
    rowValuesHasType: rowValues && typeof rowValues === 'object' && 'type' in rowValues,
    rowValuesTypeField: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type : undefined,
    rowValuesTypeType: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null && 'type' in (rowValues as any).type ? ((rowValues as any).type as any).type : undefined,
    rowValuesTypeIsNull: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type === null : false,
    rowValuesTypeIsUndefined: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type === undefined : false,
    rowValuesTypeTypeIsNull: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null && 'type' in (rowValues as any).type ? ((rowValues as any).type as any).type === null : false,
    rowValuesTypeTypeIsUndefined: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null && 'type' in (rowValues as any).type ? ((rowValues as any).type as any).type === undefined : false,
    columnsLength: columns?.length,
    nestedLevel,
  });

  // Filter out null/undefined columns before mapping
  const validColumns = columns.filter((col) => col !== null && col !== undefined);

  // Debug: log if we found null columns
  if (validColumns.length !== columns.length) {
    // eslint-disable-next-line no-console
    console.error('Table TableRow found null columns in columns array', {
      totalColumns: columns.length,
      validColumns: validColumns.length,
      columns,
      rowKey: columnKey,
    });
  }

  const fields = validColumns.map(({ field }) => field);
  const expandingButton = (
    <ExpandingButton
      rowKey={columnKey}
      expandedRows={expandedRows}
      onExpand={onExpand}
      onCollapse={onCollapse}
      rowValues={rowValues}
      onClick={setExpandedRows}
      nestedLevel={nestedLevel}
    />
  );
  const handleRowClick = () => {
    onRowClick?.(rowValues, columnKey);
  };

  const rowClasses = `ams-table-row ${
    rowValues.isNestedColumn ? 'is-nested-column-row' : ''
  } ${currentSelectedKey === columnKey ? 'is-selected-row' : ''} ${
    onRowClick ? 'is-interactive-row' : ''
  }`;

  return (
    <React.Fragment key={columnKey}>
      <tr
        className={rowClasses}
        key={columnKey}
        style={rowStyles}
        ref={expandRowRef}
        onClick={handleRowClick}
      >
        <>
          {(() => {
            try {
              // EXTREME LOGGING: Log before mapping over rowValues
              // eslint-disable-next-line no-console
              console.log('🔴🔴🔴 TableRow: STEP 13 - Before mapping rowValues - EXTREME LOGGING', {
                timestamp: new Date().toISOString(),
                columnKey,
                rowValues: rowValues,
                rowValuesStringified: JSON.stringify(rowValues),
                rowValuesType: typeof rowValues,
                rowValuesIsNull: rowValues === null,
                rowValuesIsUndefined: rowValues === undefined,
                rowValuesKeys: rowValues && typeof rowValues === 'object' ? Object.keys(rowValues) : 'not an object',
                rowValuesEntries: rowValues && typeof rowValues === 'object' ? Object.entries(rowValues).map(([k, v]) => ({
                  key: k,
                  value: v,
                  valueType: typeof v,
                  isNull: v === null,
                  isUndefined: v === undefined,
                  isObject: typeof v === 'object' && v !== null,
                  objectKeys: (typeof v === 'object' && v !== null) ? Object.keys(v) : [],
                  objectEntries: (typeof v === 'object' && v !== null) ? Object.entries(v).map(([k2, v2]) => ({
                    key: k2,
                    value: v2,
                    valueType: typeof v2,
                    isNull: v2 === null,
                    isUndefined: v2 === undefined,
                  })) : [],
                })) : 'not an object',
                fields,
                typeFieldValue: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type : 'NO TYPE PROPERTY',
                typeFieldValueStringified: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? JSON.stringify((rowValues as any).type) : 'NO TYPE PROPERTY',
                typeFieldType: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? typeof (rowValues as any).type : 'NO TYPE PROPERTY',
                typeFieldIsNull: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type === null : 'NO TYPE PROPERTY',
                typeFieldIsUndefined: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? (rowValues as any).type === undefined : 'NO TYPE PROPERTY',
                typeFieldIsObject: rowValues && typeof rowValues === 'object' && 'type' in rowValues ? typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null : 'NO TYPE PROPERTY',
                typeFieldKeys: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null ? Object.keys((rowValues as any).type) : 'NO TYPE PROPERTY OR NOT OBJECT',
                typeFieldEntries: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null ? Object.entries((rowValues as any).type).map(([k, v]) => ({
                  key: k,
                  value: v,
                  valueType: typeof v,
                  isNull: v === null,
                  isUndefined: v === undefined,
                })) : 'NO TYPE PROPERTY OR NOT OBJECT',
                typeFieldHasTypeProperty: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null && 'type' in (rowValues as any).type,
                typeFieldTypeProperty: rowValues && typeof rowValues === 'object' && 'type' in rowValues && typeof (rowValues as any).type === 'object' && (rowValues as any).type !== null && 'type' in (rowValues as any).type ? ((rowValues as any).type as any).type : 'NO TYPE.TYPE PROPERTY',
                callStack: new Error().stack,
              });

              return Object.entries(rowValues)
                .filter(([key]) => fields.includes(key))
                .map(([key, value], rowIndex) => {
  // EXTREME LOGGING: Log each field being processed
  // eslint-disable-next-line no-console
  console.log(`🔴🔴🔴 TableRow: STEP 14 - Processing field ${key} (index ${rowIndex}) - EXTREME LOGGING`, {
    timestamp: new Date().toISOString(),
                columnKey,
                key,
                value,
                valueType: typeof value,
                rowIndex,
                isTypeField: key === 'type',
                typeValue: key === 'type' ? value : undefined,
                typeValueType: key === 'type' && value ? typeof value : undefined,
                typeValueIsNull: key === 'type' && value === null,
                typeValueIsUndefined: key === 'type' && value === undefined,
                typeValueTypeProperty: key === 'type' && value && typeof value === 'object' && value !== null && 'type' in value ? (value as any).type : undefined,
              });

              // Comprehensive logging for type field
              if (key === 'type') {
                if (value === null || value === undefined) {
                  // eslint-disable-next-line no-console
                  console.error('🔴 Table TableRow: NULL TYPE FIELD DETECTED', {
                    key,
                    value,
                    valueType: typeof value,
                    rowIndex,
                    rowKey: columnKey,
                    rowName: rowValues?.name,
                    fullRowValues: JSON.parse(JSON.stringify(rowValues)), // Deep clone for inspection
                    columnInfo: validColumns.find(({ field }) => field === key),
                    allFields: Object.keys(rowValues),
                    allFieldValues: Object.entries(rowValues).map(([k, v]) => ({
                      field: k,
                      value: v,
                      valueType: typeof v,
                      isNull: v === null,
                      isUndefined: v === undefined,
                    })),
                  });
                } else if (value && typeof value === 'object' && 'type' in value && ((value as any).type === null || (value as any).type === undefined)) {
                  // eslint-disable-next-line no-console
                  console.error('🔴 Table TableRow: TYPE OBJECT HAS NULL .type PROPERTY', {
                    key,
                    value,
                    valueType: typeof value,
                    valueTypeType: 'type' in value ? (value as any).type : undefined,
                    rowIndex,
                    rowKey: columnKey,
                    rowName: rowValues?.name,
                    fullRowValues: JSON.parse(JSON.stringify(rowValues)),
                    typeObjectKeys: value ? Object.keys(value) : [],
                    typeObjectValues: value ? Object.entries(value).map(([k, v]) => ({
                      key: k,
                      value: v,
                      valueType: typeof v,
                      isNull: v === null,
                    })) : [],
                  });
                }
              }

              const columnInfo = validColumns.find(({ field }) => field === key);
              const horAlign: TextAlignmentValues = columnInfo
                ? columnInfo.horAlign || DEFAULT_TEXT_ALIGNMENT
                : DEFAULT_TEXT_ALIGNMENT;
              const width =
                columnInfo && columnInfo.width
                  ? `${columnInfo.width}px`
                  : DEFAULT_CELL_WIDTH;
              // TODO: Improve the typing of this
              let cellContent: React.ReactNode | typeof value = value;

              if (columnInfo && columnInfo.component) {
                try {
                  // Additional safety check before calling component
                  if (value === null && key === 'type') {
                    // eslint-disable-next-line no-console
                    console.error('🔴 Table TableRow: Rendering placeholder for null type', {
                      key,
                      value,
                      rowIndex,
                      rowKey: columnKey,
                      rowValues: JSON.parse(JSON.stringify(rowValues)),
                    });
                    cellContent = <div className="resource-type">-</div>;
                  } else {
                    cellContent = columnInfo.component(value, rowIndex, rowValues);
                  }
                } catch (componentError) {
                  // eslint-disable-next-line no-console
                  console.error('🔴 Table TableRow: ERROR IN COMPONENT RENDERER', {
                    error: componentError,
                    errorMessage: componentError?.message,
                    errorStack: componentError?.stack,
                    key,
                    value,
                    valueType: typeof value,
                    rowIndex,
                    rowKey: columnKey,
                    rowName: rowValues?.name,
                    fullRowValues: JSON.parse(JSON.stringify(rowValues)),
                    columnInfo,
                  });
                  // Render a safe fallback
                  cellContent = <div className="resource-type">-</div>;
                }
              }

              const isFirstCell =
                fields.findIndex((field) => field === key) === 0;
              const hasExpandingButton = isFirstCell && rowValues.isExpandable;

              let cellStyle;

              if (isFirstCell) {
                cellStyle = {
                  width,
                  paddingLeft: getIndentationPaddingSize(
                    nestedLevel,
                    rowValues.isExpandable
                  ),
                };
              } else {
                cellStyle = { width };
              }

              return (
                <td
                  className={`ams-table-cell ${getCellAlignmentClass(
                    horAlign
                  )}`}
                  key={`index:${rowIndex}`}
                  style={cellStyle}
                >
                  <span
                    className={`${
                      isFirstCell ? 'ams-table-first-cell-contents' : ''
                    }`}
                  >
                    {hasExpandingButton && expandingButton}
                    {cellContent}
                  </span>
                </td>
              );
            });
            } catch (mapError) {
              // eslint-disable-next-line no-console
              console.error('🔴 Table TableRow: ERROR IN MAP OPERATION', {
                error: mapError,
                errorMessage: mapError?.message,
                errorStack: mapError?.stack,
                rowKey: columnKey,
                rowValues: rowValues ? JSON.parse(JSON.stringify(rowValues)) : null,
                fields,
                validColumnsLength: validColumns.length,
              });
              return <td colSpan={fields.length} className="ams-table-cell">Error rendering row</td>;
            }
          })()}
        </>
      </tr>
    </React.Fragment>
  );
};

type RowKey = string;

const getTableRows = (tableRowDetails: TableRowDetails) => {
  const {
    data,
    columns,
    currentSelectedKey,
    preExpandPanelKey,
    rowStyles,
    onExpand,
    onCollapse,
    onRowClick,
    expandRowRef,
    expandedRows,
    setExpandedRows,
    formatChildrenData,
    preExpandRightPanel,
    nestedLevel,
  } = tableRowDetails;

  // STEP 10: Log data received by Table component
  // eslint-disable-next-line no-console
  console.log('🔵 Table: STEP 10 - Data received in getTableRows', {
    dataLength: data?.length,
    data,
    dataType: typeof data,
    isArray: Array.isArray(data),
    hasNullItems: data?.some((item) => item === null || item === undefined),
    dataDetails: data?.map((item, idx) => ({
      index: idx,
      key: item?.key,
      name: item?.name,
      hasType: item && typeof item === 'object' && 'type' in item,
      type: item && typeof item === 'object' && 'type' in item ? (item as any).type : undefined,
      typeType: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type : undefined,
      typeIsNull: item && typeof item === 'object' && 'type' in item ? (item as any).type === null : false,
      typeIsUndefined: item && typeof item === 'object' && 'type' in item ? (item as any).type === undefined : false,
      typeTypeIsNull: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type === null : false,
      typeTypeIsUndefined: item && typeof item === 'object' && 'type' in item && typeof (item as any).type === 'object' && (item as any).type !== null && 'type' in (item as any).type ? ((item as any).type as any).type === undefined : false,
    })),
    columnsLength: columns?.length,
    nestedLevel,
  });

  const result = data.reduce((prevRows, item: FormattedDataType, itemIndex: number) => {
    // EXTREME LOGGING: Log each item being processed in reduce
    // eslint-disable-next-line no-console
    console.log(`🔴🔴🔴 Table: STEP 11 - Processing item ${itemIndex} in reduce - EXTREME LOGGING`, {
      timestamp: new Date().toISOString(),
      itemIndex,
      item: item,
      itemStringified: JSON.stringify(item),
      itemType: typeof item,
      itemIsNull: item === null,
      itemIsUndefined: item === undefined,
      itemKeys: item && typeof item === 'object' ? Object.keys(item) : 'not an object',
      itemEntries: item && typeof item === 'object' ? Object.entries(item).map(([k, v]) => ({
        key: k,
        value: v,
        valueType: typeof v,
        isNull: v === null,
        isUndefined: v === undefined,
        isObject: typeof v === 'object' && v !== null,
        objectKeys: (typeof v === 'object' && v !== null) ? Object.keys(v) : [],
        objectEntries: (typeof v === 'object' && v !== null) ? Object.entries(v).map(([k2, v2]) => ({
          key: k2,
          value: v2,
          valueType: typeof v2,
          isNull: v2 === null,
          isUndefined: v2 === undefined,
        })) : [],
      })) : 'not an object',
      itemKey: item?.key,
      itemName: item?.name,
      hasType: item && typeof item === 'object' && 'type' in item,
      type: item && typeof item === 'object' && 'type' in item ? (item as any).type : 'NO TYPE PROPERTY',
      typeStringified: item && typeof item === 'object' && 'type' in item ? JSON.stringify((item as any).type) : 'NO TYPE PROPERTY',
      typeTypeValue: typeof (item && typeof item === 'object' && 'type' in item ? (item as any).type : undefined),
      typeIsNull: item && typeof item === 'object' && 'type' in item ? (item as any).type === null : 'NO TYPE PROPERTY',
      typeIsUndefined: item && typeof item === 'object' && 'type' in item ? (item as any).type === undefined : 'NO TYPE PROPERTY',
      typeIsObject: item && typeof item === 'object' && 'type' in item ? typeof (item as any).type === 'object' && (item as any).type !== null : 'NO TYPE PROPERTY',
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
      prevRowsLength: prevRows.length,
      prevRows: prevRows,
      callStack: new Error().stack,
    });
    try {
      // Debug logging: catch any null items or items with null type before processing
      if (!item || item === null) {
        // eslint-disable-next-line no-console
        console.error('Table getTableRows received null item in data array', {
          dataLength: data.length,
          itemIndex,
          item,
          allData: data,
        });
        return prevRows;
      }

      if (!item.type || item.type === null) {
        // eslint-disable-next-line no-console
        console.error('🔴 Table getTableRows: ITEM HAS NULL TYPE FIELD', {
          itemIndex,
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
      });
      }

    if (item.key && item.key === preExpandPanelKey && preExpandRightPanel) {
      preExpandRightPanel(item);
    }

    const parentRow = (
      <TableRow
        key={item.key}
        columnKey={item.key}
        currentSelectedKey={currentSelectedKey}
        columns={columns}
        rowValues={item}
        rowStyles={rowStyles}
        onExpand={onExpand}
        onCollapse={onCollapse}
        onRowClick={onRowClick}
        expandRowRef={
          item.key && item.key === preExpandPanelKey ? expandRowRef : undefined
        }
        expandedRows={expandedRows}
        setExpandedRows={setExpandedRows}
        nestedLevel={nestedLevel}
      />
    );

    if (
      item.isExpandable &&
      expandedRows.includes(item.key) &&
      formatChildrenData
    ) {
      // STEP 17: Log when processing expandable item
      // eslint-disable-next-line no-console
      console.log('🟠 Table: STEP 17 - Processing expandable item', {
        itemKey: item.key,
        itemName: item.name,
        itemIsExpandable: item.isExpandable,
        isExpanded: expandedRows.includes(item.key),
        hasFormatChildrenData: !!formatChildrenData,
      });

      const { rowValuesToDisplay, formattedChildren, arrayCount } =
        handleSpecificTypeRowData(item, formatChildrenData);

      // eslint-disable-next-line no-console
      console.log('🟠 Table: STEP 17a - After handleSpecificTypeRowData', {
        rowValuesToDisplay,
        rowValuesToDisplayKey: rowValuesToDisplay?.key,
        rowValuesToDisplayHasType: rowValuesToDisplay && typeof rowValuesToDisplay === 'object' && 'type' in rowValuesToDisplay,
        rowValuesToDisplayType: rowValuesToDisplay && typeof rowValuesToDisplay === 'object' && 'type' in rowValuesToDisplay ? (rowValuesToDisplay as any).type : undefined,
        formattedChildrenLength: formattedChildren.length,
        formattedChildren,
        formattedChildrenWithNullType: formattedChildren.filter((fc) => !fc || typeof fc !== 'object' || !('type' in fc) || (fc as any).type === null),
        arrayCount,
      });

      const additionalTableColCount = columns.length - 1;
      const openerRow = getSpecificTypeOpenerRow(
        rowValuesToDisplay,
        arrayCount,
        nestedLevel,
        additionalTableColCount
      );
      const closerRow = getSpecificTypeCloserRow(
        rowValuesToDisplay,
        arrayCount,
        nestedLevel,
        additionalTableColCount
      );

      return [
        ...prevRows,
        parentRow,
        openerRow,
        ...(() => {
          // STEP 18: Log before recursive getTableRows call
          // eslint-disable-next-line no-console
          console.log('🟠 Table: STEP 18 - Calling getTableRows recursively for children', {
            formattedChildrenLength: formattedChildren.length,
            formattedChildren,
            formattedChildrenWithNullType: formattedChildren.filter((fc) => !fc || typeof fc !== 'object' || !('type' in fc) || (fc as any).type === null),
            nestedLevel: nestedLevel + 1,
          });

          // Final safety check: ensure all formattedChildren have valid type objects
          const safeFormattedChildren = formattedChildren.map((fc, fcIdx) => {
            if (!fc || typeof fc !== 'object' || !('type' in fc) || (fc as any).type === null) {
              // eslint-disable-next-line no-console
              console.error('🔴 Table: STEP 18 - Found invalid child, fixing', {
                fcIdx,
                fc,
                fcType: fc && typeof fc === 'object' && 'type' in fc ? (fc as any).type : undefined,
              });
              return {
                ...fc,
                type: {
                  type: '',
                  name: (fc as any)?.name || '',
                  database: '',
                },
              };
            }
            return fc;
          });

          try {
            const nestedRows = getTableRows({
              ...tableRowDetails,
              data: safeFormattedChildren,
              nestedLevel: nestedLevel + 1,
            });

            // eslint-disable-next-line no-console
            console.log('🟠 Table: STEP 18a - Recursive getTableRows returned', {
              nestedRowsLength: nestedRows.length,
              nestedRows,
            });

            return nestedRows;
          } catch (error) {
            // eslint-disable-next-line no-console
            console.error('🔴 Table: STEP 18 - Error in recursive getTableRows', {
              error,
              errorMessage: error?.message,
              errorStack: error?.stack,
              safeFormattedChildren,
            });
            return [];
          }
        })(),
        closerRow,
      ];
    }

      const result = [...prevRows, parentRow];

      // STEP 19: Log the result array to check for null items
      // eslint-disable-next-line no-console
      console.log(`🟠 Table: STEP 19 - Result after processing item ${itemIndex}`, {
        itemIndex,
        resultLength: result.length,
        resultHasNullItems: result.some((r) => r === null || r === undefined),
        resultItems: result.map((r, ridx) => ({
          index: ridx,
          isNull: r === null,
          isUndefined: r === undefined,
          type: typeof r,
        })),
      });

      return result;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('🔴 Table getTableRows: ERROR PROCESSING ITEM', {
        error,
        errorMessage: error?.message,
        errorStack: error?.stack,
        itemIndex,
        item,
        itemType: item?.type,
        itemTypeType: item?.type?.type,
        itemKey: item?.key,
        itemName: item?.name,
        itemIsNull: item === null,
        itemIsUndefined: item === undefined,
        itemHasType: 'type' in (item || {}),
        itemTypeIsNull: item?.type === null,
        itemTypeIsUndefined: item?.type === undefined,
        fullItem: item ? JSON.parse(JSON.stringify(item)) : null, // Deep clone for inspection
        itemKeys: item ? Object.keys(item) : [],
        itemEntries: item ? Object.entries(item).map(([k, v]) => ({
          key: k,
          value: v,
          valueType: typeof v,
          isNull: v === null,
          isUndefined: v === undefined,
          isObject: typeof v === 'object' && v !== null,
          objectKeys: (typeof v === 'object' && v !== null) ? Object.keys(v) : [],
        })) : [],
        dataLength: data.length,
        allDataIndices: data.map((d, idx) => ({
          index: idx,
          key: d?.key,
          name: d?.name,
          hasType: 'type' in (d || {}),
          typeIsNull: d?.type === null,
          typeIsUndefined: d?.type === undefined,
        })),
      });
      return prevRows;
    }
  }, []);

  // STEP 20: Log final result before returning
  // eslint-disable-next-line no-console
  console.log('🟠 Table: STEP 20 - Final result from getTableRows', {
    resultLength: result.length,
    resultHasNullItems: result.some((r) => r === null || r === undefined),
    resultItems: result.map((r, ridx) => ({
      index: ridx,
      isNull: r === null,
      isUndefined: r === undefined,
      type: typeof r,
    })),
  });

  // Final safety check: filter out any null items
  const safeResult = result.filter((r) => {
    const isValid = r !== null && r !== undefined;
    if (!isValid) {
      // eslint-disable-next-line no-console
      console.error('🔴 Table: STEP 20 - Filtered out null item from final result', { r });
    }
    return isValid;
  });

  return safeResult;
};

const useTableHooks = ({
  data,
  maxNumRows,
  preExpandPanelKey,
  tableKey,
  shouldExpandAllRows,
  toggleExpandingRows,
}: TableHooksInput) => {
  const allColumnKeys = React.useMemo(() => getAllColumnKeys(data), [data]);
  const initialExpandedRows = React.useMemo(
    () =>
      getInitialExpandedRows(
        data,
        allColumnKeys,
        maxNumRows,
        preExpandPanelKey,
        tableKey
      ),
    [preExpandPanelKey]
  );

  const [expandedRows, setExpandedRows] =
    React.useState<RowKey[]>(initialExpandedRows);

  React.useEffect(() => {
    expandOrCollapseAllRows({
      allColumnKeys,
      shouldExpandAllRows,
      setExpandedRows,
      initialExpandedRows,
      maxNumRows,
      toggleExpandingRows,
    });
  }, [shouldExpandAllRows]);

  const expandRowRef = React.useRef<HTMLTableRowElement>(null);

  React.useEffect(() => {
    if (expandRowRef.current !== null) {
      expandRowRef.current.scrollIntoView({ block: SCROLL_INTO_VIEW_BLOCK });
    }
  }, []);

  return { expandedRows, setExpandedRows, expandRowRef };
};

const Table: React.FC<TableProps> = ({
  data,
  columns,
  options = {},
}: TableProps) => {
  const {
    tableClassName = '',
    isLoading = false,
    numLoadingBlocks = DEFAULT_LOADING_ITEMS,
    rowHeight = DEFAULT_ROW_HEIGHT,
    emptyMessage,
    onExpand,
    onCollapse,
    onRowClick,
    preExpandPanelKey,
    currentSelectedKey,
    tableKey,
    formatChildrenData,
    preExpandRightPanel,
    maxNumRows,
    shouldExpandAllRows,
    toggleExpandingRows,
    hasRowsToExpand,
  } = options;
  const fields = columns.map(({ field }) => field);
  const rowStyles = { height: `${rowHeight}px` };

  const { expandedRows, setExpandedRows, expandRowRef } = useTableHooks({
    data,
    maxNumRows,
    preExpandPanelKey,
    tableKey,
    shouldExpandAllRows,
    toggleExpandingRows,
  });

  let body: React.ReactNode = (
    <EmptyRow
      colspan={fields.length}
      rowStyles={rowStyles}
      emptyMessage={emptyMessage}
    />
  );

  if (data.length) {
    if (!checkIfValidData(data, fields)) {
      throw new Error(INVALID_DATA_ERROR_MESSAGE);
    }

    body = getTableRows({
      data,
      columns,
      currentSelectedKey,
      preExpandPanelKey,
      rowStyles,
      onExpand,
      onCollapse,
      onRowClick,
      expandRowRef,
      expandedRows,
      setExpandedRows,
      formatChildrenData,
      preExpandRightPanel,
      nestedLevel: 0,
    });
  }

  let header: React.ReactNode = (
    <tr>
      {columns.map(
        ({ title, horAlign = DEFAULT_TEXT_ALIGNMENT, width = null }, index) => {
          const cellStyle = {
            width: width ? `${width}px` : DEFAULT_CELL_WIDTH,
          };

          return (
            <th
              className={`ams-table-heading-cell ${getCellAlignmentClass(
                horAlign
              )}`}
              key={`index:${index}`}
              style={cellStyle}
            >
              <span
                className={`${
                  index === 0 ? 'ams-table-first-cell-contents' : ''
                }`}
              >
                {index === 0 && (
                  <ExpandCollapseAllButton
                    shouldExpandAllRows={shouldExpandAllRows}
                    hasRowsToExpand={hasRowsToExpand}
                    toggleExpandingRows={toggleExpandingRows}
                  />
                )}
                {title}
              </span>
            </th>
          );
        }
      )}
    </tr>
  );

  if (isLoading) {
    header = <ShimmeringHeader />;
    body = <ShimmeringBody numLoadingBlocks={numLoadingBlocks} />;
  }

  return (
    <table className={`ams-table ${tableClassName || ''}`}>
      <thead className="ams-table-header">{header}</thead>
      <tbody className="ams-table-body">{body}</tbody>
    </table>
  );
};

export default Table;
