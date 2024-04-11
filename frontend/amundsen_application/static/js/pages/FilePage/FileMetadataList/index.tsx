// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import FileMetadataListItem from '../FileMetadataListItem';
import { FileMetadataListItemProps } from '../FileMetadataListItem';

import './styles.scss';

export interface FileMetadataListProps {
  file_metadata: FileMetadataListItemProps[];
}

class FileMetadataList extends React.Component<FileMetadataListProps> {
  render() {
    const { file_metadata } = this.props;

    if (file_metadata.length === 0) {
      return null;
    }

    const filemetadataList = file_metadata.map(({ name, content }) => (
      <FileMetadataListItem
        name={name}
        content={content}
      />
    ));

    return (
      <ul className="filemetadata-list list-group" role="tablist">
        {filemetadataList}
      </ul>
    );
  }
}

export default FileMetadataList;
