// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Modal, OverlayTrigger, Popover } from 'react-bootstrap';

import './styles.scss';

import { logClick } from 'utils/analytics';
import {
  getTruncatedText,
  parseNestedType,
  NestedType,
  ParsedType,
} from './parser';
import {
  CTA_TEXT,
  MODAL_TITLE,
  TEXT_INDENT,
  MAX_DISPLAY_TYPE_LENGTH,
} from './constants';

export interface ColumnTypeProps {
  columnName: string;
  database: string;
  type: string;
}

export interface ColumnTypeState {
  showModal: boolean;
}

export class ColumnType extends React.Component<
  ColumnTypeProps,
  ColumnTypeState
> {
  constructor(props) {
    super(props);

    this.state = {
      showModal: false,
    };
  }

  nestedType: NestedType | null;

  hideModal = (e) => {
    this.stopPropagation(e);
    this.setState({ showModal: false });
  };

  showModal = (e) => {
    logClick(e);
    this.stopPropagation(e);
    this.setState({ showModal: true });
  };

  stopPropagation = (e) => {
    if (e) {
      e.stopPropagation();
    }
  };

  createLineItem = (text: string, textIndent: number) => (
    <div key={`lineitem:${text}`} style={{ textIndent: `${textIndent}px` }}>
      {text}
    </div>
  );

  renderParsedChildren = (children: ParsedType[], level: number) => {
    // EXTREME LOGGING: Log when rendering parsed children
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType renderParsedChildren - EXTREME LOGGING', {
      timestamp: new Date().toISOString(),
      children: children,
      childrenLength: children?.length,
      childrenType: typeof children,
      childrenIsArray: Array.isArray(children),
      childrenStringified: JSON.stringify(children),
      level,
      callStack: new Error().stack,
    });

    const textIndent = level * TEXT_INDENT;

    if (!children || !Array.isArray(children)) {
      // eslint-disable-next-line no-console
      console.error('🔴🔴🔴 ColumnType renderParsedChildren: Invalid children', {
        children,
        childrenType: typeof children,
        childrenIsArray: Array.isArray(children),
        callStack: new Error().stack,
      });
      return [];
    }

    return children
      .filter((item, filterIdx) => {
        const isValid = item !== null && item !== undefined;
        // EXTREME LOGGING: Log every filter check
        // eslint-disable-next-line no-console
        console.log(`🔴🔴🔴 ColumnType renderParsedChildren: Filtering item ${filterIdx}`, {
          timestamp: new Date().toISOString(),
          filterIdx,
          item,
          itemType: typeof item,
          itemIsNull: item === null,
          itemIsUndefined: item === undefined,
          isValid,
          willKeep: isValid,
        });
        if (!isValid) {
          // eslint-disable-next-line no-console
          console.error('🔴🔴🔴 ColumnType renderParsedChildren: Filtered out null item', {
            filterIdx,
            item,
            callStack: new Error().stack,
          });
        }
        return isValid;
      })
      .map((item, mapIdx) => {
        // EXTREME LOGGING: Log every map iteration
        // eslint-disable-next-line no-console
        console.log(`🔴🔴🔴 ColumnType renderParsedChildren: Mapping item ${mapIdx}`, {
          timestamp: new Date().toISOString(),
          mapIdx,
          item,
          itemType: typeof item,
          itemIsString: typeof item === 'string',
          itemIsObject: typeof item === 'object' && item !== null,
          itemStringified: JSON.stringify(item),
          itemKeys: typeof item === 'object' && item !== null ? Object.keys(item) : 'not an object',
          itemEntries: typeof item === 'object' && item !== null ? Object.entries(item).map(([k, v]) => ({
            key: k,
            value: v,
            valueType: typeof v,
            isNull: v === null,
            isUndefined: v === undefined,
          })) : 'not an object',
          callStack: new Error().stack,
        });

        try {
          if (typeof item === 'string') {
            // eslint-disable-next-line no-console
            console.log(`🔴🔴🔴 ColumnType renderParsedChildren: Item ${mapIdx} is string, creating line item`, {
              mapIdx,
              item,
              textIndent,
            });
            return this.createLineItem(item, textIndent);
          }

          // EXTREME LOGGING: Before calling renderNestedType
          // eslint-disable-next-line no-console
          console.log(`🔴🔴🔴 ColumnType renderParsedChildren: Item ${mapIdx} is object, calling renderNestedType`, {
            mapIdx,
            item,
            itemType: typeof item,
            itemIsNull: item === null,
            itemIsUndefined: item === undefined,
            itemKeys: typeof item === 'object' && item !== null ? Object.keys(item) : 'not an object',
            level,
          });

          const result = this.renderNestedType(item, level);

          // eslint-disable-next-line no-console
          console.log(`🔴🔴🔴 ColumnType renderParsedChildren: renderNestedType returned for item ${mapIdx}`, {
            mapIdx,
            result,
            resultType: typeof result,
            resultIsNull: result === null,
          });

          return result;
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('🔴🔴🔴 ColumnType renderParsedChildren: ERROR in map callback', {
            error,
            errorMessage: error?.message,
            errorStack: error?.stack,
            mapIdx,
            item,
            itemType: typeof item,
            itemStringified: JSON.stringify(item),
            callStack: new Error().stack,
          });
          return null;
        }
      })
      .filter((result) => result !== null && result !== undefined);
  };

  renderNestedType = (nestedType: NestedType, level: number = 0) => {
    // EXTREME LOGGING: Log when rendering nested type
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType renderNestedType - EXTREME LOGGING', {
      timestamp: new Date().toISOString(),
      nestedType,
      nestedTypeType: typeof nestedType,
      nestedTypeIsNull: nestedType === null,
      nestedTypeIsUndefined: nestedType === undefined,
      nestedTypeStringified: JSON.stringify(nestedType),
      nestedTypeKeys: nestedType && typeof nestedType === 'object' ? Object.keys(nestedType) : 'not an object',
      nestedTypeEntries: nestedType && typeof nestedType === 'object' ? Object.entries(nestedType).map(([k, v]) => ({
        key: k,
        value: v,
        valueType: typeof v,
        isNull: v === null,
        isUndefined: v === undefined,
      })) : 'not an object',
      level,
      callStack: new Error().stack,
    });

    if (!nestedType || nestedType === null) {
      // eslint-disable-next-line no-console
      console.error('🔴🔴🔴 ColumnType renderNestedType: NULL nestedType, returning null', {
        nestedType,
        nestedTypeType: typeof nestedType,
        level,
        callStack: new Error().stack,
      });
      return null;
    }

    // EXTREME LOGGING: Before destructuring
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType renderNestedType: Before destructuring', {
      nestedType,
      hasHead: 'head' in nestedType,
      hasTail: 'tail' in nestedType,
      hasChildren: 'children' in nestedType,
      head: nestedType.head,
      tail: nestedType.tail,
      children: nestedType.children,
      childrenType: typeof nestedType.children,
      childrenIsArray: Array.isArray(nestedType.children),
      childrenLength: Array.isArray(nestedType.children) ? nestedType.children.length : 'not an array',
    });

    const { head, tail, children } = nestedType;
    const textIndent = level * TEXT_INDENT;

    // EXTREME LOGGING: After destructuring
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType renderNestedType: After destructuring', {
      head,
      headType: typeof head,
      headIsNull: head === null,
      headIsUndefined: head === undefined,
      tail,
      tailType: typeof tail,
      tailIsNull: tail === null,
      tailIsUndefined: tail === undefined,
      children,
      childrenType: typeof children,
      childrenIsArray: Array.isArray(children),
      childrenLength: Array.isArray(children) ? children.length : 'not an array',
      textIndent,
      level,
    });

    return (
      <div key={`nesteditem:${head}${tail}`}>
        {this.createLineItem(head, textIndent)}
        {this.renderParsedChildren(children || [], level + 1)}
        {this.createLineItem(tail, textIndent)}
      </div>
    );
  };

  render = () => {
    const { showModal } = this.state;
    const { columnName, database, type } = this.props;

    // EXTREME LOGGING: Log when ColumnType renders
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType render - EXTREME LOGGING', {
      timestamp: new Date().toISOString(),
      columnName,
      database,
      type,
      typeType: typeof type,
      typeIsNull: type === null,
      typeIsUndefined: type === undefined,
      callStack: new Error().stack,
    });

    // EXTREME LOGGING: Before calling parseNestedType
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType render: Before parseNestedType', {
      type,
      database,
      willCallParseNestedType: true,
    });

    this.nestedType = parseNestedType(type, database);

    // EXTREME LOGGING: After calling parseNestedType
    // eslint-disable-next-line no-console
    console.log('🔴🔴🔴 ColumnType render: After parseNestedType', {
      nestedType: this.nestedType,
      nestedTypeType: typeof this.nestedType,
      nestedTypeIsNull: this.nestedType === null,
      nestedTypeIsUndefined: this.nestedType === undefined,
      nestedTypeStringified: this.nestedType ? JSON.stringify(this.nestedType) : 'null/undefined',
      nestedTypeKeys: this.nestedType && typeof this.nestedType === 'object' ? Object.keys(this.nestedType) : 'not an object',
      nestedTypeEntries: this.nestedType && typeof this.nestedType === 'object' ? Object.entries(this.nestedType).map(([k, v]) => ({
        key: k,
        value: v,
        valueType: typeof v,
        isNull: v === null,
        isUndefined: v === undefined,
      })) : 'not an object',
    });

    if (this.nestedType === null) {
      // eslint-disable-next-line no-console
      console.log('🔴🔴🔴 ColumnType render: nestedType is null, returning simple type', {
        type,
      });
      return <p className="column-type">{type}</p>;
    }

    const hasLongTypeString =
      this.nestedType.col_type &&
      this.nestedType.col_type.length > MAX_DISPLAY_TYPE_LENGTH;
    const popoverHover = (
      <Popover
        className="column-type-popover"
        id={`column-type-popover:${columnName}`}
      >
        {CTA_TEXT}
      </Popover>
    );

    return (
      <div onClick={this.stopPropagation}>
        <OverlayTrigger
          trigger={['hover', 'focus']}
          placement="top"
          overlay={popoverHover}
          rootClose
        >
          <button
            data-type="column-type"
            type="button"
            className="column-type-btn"
            onClick={this.showModal}
          >
            {this.nestedType.col_type && !hasLongTypeString
              ? this.nestedType.col_type
              : getTruncatedText(this.nestedType)}
          </button>
        </OverlayTrigger>
        <Modal
          className="column-type-modal"
          show={showModal}
          onHide={this.hideModal}
        >
          <Modal.Header closeButton>
            <Modal.Title>
              <div className="main-title">{MODAL_TITLE}</div>
              <div className="sub-title">{columnName}</div>
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <div className="column-type-modal-content">
              {this.renderNestedType(this.nestedType)}
            </div>
          </Modal.Body>
        </Modal>
      </div>
    );
  };
}

export default ColumnType;
