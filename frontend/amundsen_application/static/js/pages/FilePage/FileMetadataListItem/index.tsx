// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { useEffect, useRef, useState } from 'react';
import { withRouter, RouteComponentProps } from 'react-router-dom'; // Import withRouter
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

const FileMetadataListItem = withRouter(({ name, content, history, location }: FileMetadataListItemProps & RouteComponentProps) => {
  const [isExpanded, setExpanded] = useState(false);
  const key = `key:${name}`;
  const itemRef = useRef<HTMLLIElement>(null); // Create a ref for the item

  function toUrlSafeString(str) {
    // Replace any character that is not a letter, number, or underscore with an underscore
    return str.replace(/[\W]+/g, '_');
  }

  const toggleExpand = (key) => {
    let _isExpanded = !isExpanded;
    setExpanded(_isExpanded);

    if (_isExpanded === true) {
      const safe_name = toUrlSafeString(name);

      history.push(`${location.pathname}${location.search}#${safe_name}`);
    }
    else {
      history.push(`${location.pathname}${location.search}`);
    }
  };

  useEffect(() => {
    if (isExpanded === true) {
      // Scroll the item into view if it matches the URL hash
      itemRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isExpanded]);

  useEffect(() => {
    const currentName = location.hash.replace('#', '');
    const safe_name = toUrlSafeString(name);
    if (currentName === safe_name.toString()) {
      setExpanded(true);
      // Scroll the item into view if it matches the URL hash
      // itemRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [location, name]);

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
    <li className="list-group-item filemetadata-list-item" role="tab" id={key} ref={itemRef}>
      <button
        className="filemetadata-list-header"
        aria-expanded={isExpanded}
        aria-controls={key}
        type="button"
        onClick={() => toggleExpand(key)}
      >
        <p className="filemetadata-list-item-name column-name">{name}</p>
      </button>
      {isExpanded &&
        fileMetadataContentList
      }
    </li>
  );
});

export default FileMetadataListItem;
