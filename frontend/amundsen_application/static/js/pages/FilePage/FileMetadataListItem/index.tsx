// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';
import 'features/CodeBlock/styles.scss';


export interface FileMetadataListItemContentProps {
  name: string;
  text: string;
  renderHTML: boolean;
}

export interface FileMetadataListItemProps {
  name: string;
  content: FileMetadataListItemContentProps[];
}

const LazyCodeBlock = React.lazy(() => import('features/CodeBlock/index'));

const FileMetadataBlockShimmer = () => (
  <div className="shimmer-block">
    <div className="shimmer-line shimmer-line--1 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--2 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--3 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--4 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--5 is-shimmer-animated" />
    <div className="shimmer-line shimmer-line--6 is-shimmer-animated" />
  </div>
);

const FileMetadataListItem = ({ name, content }: FileMetadataListItemProps) => {
  const [isExpanded, setExpanded] = React.useState(false);
  const toggleExpand = () => {
    setExpanded(!isExpanded);
  };
  const key = `key:${name}`;

  const fileMetadataContentList = content.map(({ name, text, renderHTML }) => (
    <label className="filemetadata-list-filemetadata-label section-title">
      {name}
      <div className="filemetadata-list-filemetadata-content">
        <React.Suspense fallback={<FileMetadataBlockShimmer />}>
          {renderHTML == true && (
            <div dangerouslySetInnerHTML={{ __html: text }} />
          )}
          {renderHTML == false && (
            <LazyCodeBlock text={text}/>
          )}
        </React.Suspense>
      </div>
    </label>
  ));

  return (
    <li className="list-group-item filemetadata-list-item" role="tab" id={key}>
      <button
        className="filemetadata-list-header"
        aria-expanded={isExpanded}
        aria-controls={key}
        type="button"
        onClick={toggleExpand}
      >
        <p className="filemetadata-list-item-name column-name">{name}</p>
      </button>
      {isExpanded &&
        fileMetadataContentList
      }
    </li>
  );
};

export default FileMetadataListItem;
