// Copyright Contributors to the Amundsen project.	/*
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import {
  getDisplayNameByResource,
  getSourceDisplayName,
} from 'config/config-utils';

import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { updateSearchState } from 'ducks/search/reducer';
import { UpdateSearchStateRequest } from 'ducks/search/types';
import { logClick } from 'utils/analytics';

import { ResourceType } from 'interfaces/Resources';
import { FileMetadata } from 'interfaces';


export interface HeaderBulletsProps {
  fileData: FileMetadata;
}
export interface DispatchFromProps {
  searchFileType: (fileType: string) => UpdateSearchStateRequest;
  searchFileCategory: (fileCategory: string) => UpdateSearchStateRequest;
  searchDataLocationType: (dataLocationType: string) => UpdateSearchStateRequest;
  searchDataLocationName: (dataLocationName: string) => UpdateSearchStateRequest;
}

export type FileHeaderBulletsProps = HeaderBulletsProps & DispatchFromProps;

export class FileHeaderBullets extends React.Component<FileHeaderBulletsProps> {
  handleFileTypeClick = (e) => {
    const { fileData, searchFileType } = this.props;

    logClick(e, {
      target_type: 'file',
      label: fileData.type,
    });
    searchFileType(fileData.type);
  };

  handleFileCategoryClick = (e) => {
    const { fileData, searchFileCategory } = this.props;

    if (fileData.category) {
      logClick(e, {
        target_type: 'file',
        label: fileData.category,
      });
      searchFileCategory(fileData.category);
    }
  };

  handleDataLocationTypeClick = (e) => {
    const { fileData, searchDataLocationType } = this.props;

    if (fileData.dataLocation) {
      logClick(e, {
        target_type: 'file',
        label: fileData.dataLocation.type,
      });
      searchDataLocationType(fileData.dataLocation.type);
    }
  };

  handleDataLocationNameClick = (e) => {
    const { fileData, searchDataLocationName } = this.props;

    if (fileData.dataLocation) {
      logClick(e, {
        target_type: 'file',
        label: fileData.dataLocation.name,
      });
      searchDataLocationName(fileData.dataLocation.name);
    }
  };

  render() {
    const { fileData } = this.props;

    return (
      <ul className="header-bullets">
        <li>{getDisplayNameByResource(ResourceType.file)}</li>
        {fileData.dataLocation && (
          <li>
            <Link to="/search" onClick={this.handleDataLocationTypeClick}>
              {fileData.dataLocation.type}
            </Link>
          </li>
        )}
        {fileData.dataLocation && (
          <li>
            <Link to="/search" onClick={this.handleDataLocationNameClick}>
              {fileData.dataLocation.name}
            </Link>
          </li>
        )}
        <li>
          <Link to="/search" onClick={this.handleFileTypeClick}>
            {getSourceDisplayName(fileData.type || '', ResourceType.file)}
          </Link>
        </li>
        {fileData.category && (
          <li>
            <Link to="/search" onClick={this.handleFileCategoryClick}>
              {fileData.category}
            </Link>
          </li>
        )}
      </ul>
    );
  }
}

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      searchFileType: (fileType: string) =>
        updateSearchState({
          filters: {
            [ResourceType.file]: { type: { value: fileType } },
          },
          submitSearch: true,
        }),
      searchFileCategory: (fileCategory: string) =>
        updateSearchState({
          filters: {
            [ResourceType.file]: { category: { value: fileCategory } },
          },
          submitSearch: true,
        }),
      searchDataLocationType: (dataLocationType: string) =>
        updateSearchState({
          filters: {
            [ResourceType.file]: { data_location_type: { value: dataLocationType } },
          },
          submitSearch: true,
        }),
      searchDataLocationName: (dataLocationName: string) =>
        updateSearchState({
          filters: {
            [ResourceType.file]: { data_location_name: { value: dataLocationName } },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<null, DispatchFromProps, HeaderBulletsProps>(
  null,
  mapDispatchToProps
)(FileHeaderBullets);
