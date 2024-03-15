// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';
import * as DocumentTitle from 'react-document-title';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { RouteComponentProps } from 'react-router';

import { GlobalState } from 'ducks/rootReducer';
import { getFileData } from 'ducks/fileMetadata/reducer';
import { openRequestDescriptionDialog } from 'ducks/notification/reducer';
import { GetFileDataRequest } from 'ducks/fileMetadata/types';
import { updateSearchState } from 'ducks/search/reducer';

import {
  getDescriptionSourceDisplayName,
  getMaxLength,
  getSourceIconClass,
  issueTrackingEnabled,
  notificationsEnabled,
  getTableLineageDefaultDepth,
} from 'config/config-utils';

import BadgeList from 'features/BadgeList';

import { AlertList } from 'components/Alert';
import BookmarkIcon from 'components/Bookmark/BookmarkIcon';
import Breadcrumb from 'features/Breadcrumb';
import EditableSection from 'components/EditableSection';
import EditableText from 'components/EditableText';
import TabsComponent, { TabInfo } from 'components/TabsComponent';
import { TAB_URL_PARAM } from 'components/TabsComponent/constants';
import TagInput from 'features/Tags/TagInput';
import LoadingSpinner from 'components/LoadingSpinner';
import { UpdateSearchStateRequest } from 'ducks/search/types';

import { logAction, logClick } from 'utils/analytics';
import { formatDateTimeShort } from 'utils/date';
import {
  getLoggingParams,
  getUrlParam,
  setUrlParam,
  FilePageParams,
} from 'utils/navigation';

import {
  ResourceType,
  RequestMetadataType,
  FileMetadata,
} from 'interfaces';
import { FormattedDataType } from 'interfaces/ColumnList';

import FileHeaderBullets from './FileHeaderBullets';

import FileDescEditableText from './FileDescEditableText';
import RequestDescriptionText from '../TableDetailPage/RequestDescriptionText';
import FileOwnerEditor from './FileOwnerEditor';

import * as Constants from './constants';
import { STATUS_CODES } from '../../constants';
import FileMetadataList from './FileMetadataList';
import { FileMetadataListItemProps, FileMetadataListItemContentProps } from './FileMetadataListItem';


import './styles.scss';


export interface PropsFromState {
  isLoading: boolean;
  statusCode: number | null;
  fileData: FileMetadata;
}
export interface DispatchFromProps {
  getFileData: (
    key: string,
    searchIndex?: string,
    source?: string
  ) => GetFileDataRequest;
  searchDataLocation: (dataLocationType: string, dataLocationName: string) => UpdateSearchStateRequest;
}

export interface MatchProps {
  uri: string;
}

export type FileProps = PropsFromState &
  DispatchFromProps &
  RouteComponentProps<MatchProps>;

const ErrorMessage = () => (
  <div className="container error-label">
    <Breadcrumb />
    <span className="text-subtitle-w1">{Constants.ERROR_MESSAGE}</span>
  </div>
);

export interface StateProps {
  currentTab: string;
  isRightPanelOpen: boolean;
  isRightPanelPreExpanded: boolean;
  isExpandCollapseAllBtnVisible: boolean;
}

export class FilePage extends React.Component<
  FileProps & RouteComponentProps<any>,
  StateProps
> {
  private key: string;

  private didComponentMount: boolean = false;

  state = {
    currentTab: this.getDefaultTab(),
    isRightPanelOpen: false,
    isRightPanelPreExpanded: false,
    isExpandCollapseAllBtnVisible: true,
  };

  componentDidMount() {
    const defaultDepth = getTableLineageDefaultDepth();
    const {
      location,
      getFileData,
    } = this.props;
    const { index, source } = getLoggingParams(location.search);
    const {
      match: { params },
    } = this.props;

    this.key = params.uri;
    getFileData(this.key, index, source);

    document.addEventListener('keydown', this.handleEscKey);
    window.addEventListener(
      'resize',
      this.handleExpandCollapseAllBtnVisibility
    );
    this.didComponentMount = true;
  }

  componentDidUpdate() {
    const {
      location,
      getFileData,
      match: { params },
    } = this.props;
    const newKey = params.uri

    if (this.key !== newKey) {
      const { index, source } = getLoggingParams(location.search);

      this.key = newKey;
      getFileData(this.key, index, source);

      // eslint-disable-next-line react/no-did-update-set-state
      this.setState({ currentTab: this.getDefaultTab() });
    }
  }

  componentWillUnmount() {
    document.removeEventListener('keydown', this.handleEscKey);
    window.removeEventListener(
      'resize',
      this.handleExpandCollapseAllBtnVisibility
    );
  }

  handleEscKey = (event: KeyboardEvent) => {
    const { isRightPanelOpen } = this.state;

    if (event.key === Constants.ESC_BUTTON_KEY && isRightPanelOpen) {
      this.toggleRightPanel(undefined);
    }
  };

  handleExpandCollapseAllBtnVisibility = () => {
    const { isRightPanelOpen } = this.state;
    const minWidth = isRightPanelOpen
      ? Constants.MIN_WIDTH_DISPLAY_BTN_WITH_OPEN_PANEL
      : Constants.MIN_WIDTH_DISPLAY_BTN;
    let newState = { isExpandCollapseAllBtnVisible: false };

    if (window.matchMedia(`(min-width: ${minWidth}px)`).matches) {
      newState = { isExpandCollapseAllBtnVisible: true };
    }
    this.setState(newState);
  };

  getDefaultTab() {
    return getUrlParam(TAB_URL_PARAM) || Constants.PROSPECTUS_FILE_TABS.FILE_TABLES;
  }

  getDisplayName() {
    const { match } = this.props;
    const { params } = match;
    return `${decodeURIComponent(params.uri)}`;
  }

  handleClick = (e) => {
    const { match, searchDataLocation } = this.props;
    const { params } = match;
    const dataLocationKey = params.uri;

    const regex = /^(.*?)\/\/(.*?)\/.*$/;
    // Execute the regular expression on the input string
    const matches = regex.exec(dataLocationKey);

    if (matches && matches.length >= 3) {
      // Extract the first and second segments
      const dataLocationType = matches[1];
      const dataLocationName = matches[2];

        logClick(e, {
          target_type: 'file',
          label: dataLocationName,
        });
        searchDataLocation(dataLocationType, dataLocationName);
    } else {
        console.log("Data Location Key does not match expected format.");
    }
  };

  preExpandRightPanel = (columnDetails: FormattedDataType) => {
    const { isRightPanelPreExpanded } = this.state;

    if (isRightPanelPreExpanded) {
      return;
    }

    let key = '';

    if (!isRightPanelPreExpanded && key) {
      this.setState({
        isRightPanelOpen: true,
        isRightPanelPreExpanded: true,
      });
    }
  };

  toggleRightPanel = (newColumnDetails: FormattedDataType | undefined) => {
    const { isRightPanelOpen } = this.state;

    let key = '';

    const shouldPanelOpen = !isRightPanelOpen;

    // if (shouldPanelOpen) {
    // }

    this.setState({
      isRightPanelOpen: shouldPanelOpen,
    });
  };

  renderProspectusTabs() {
    const tabInfo: TabInfo[] = [];
    const {
      fileData,
    } = this.props;
    const {
      currentTab,
      isRightPanelOpen,
    } = this.state;
    const fileParams: FilePageParams = {
      key: fileData.key,
      name: fileData.name
    };
    const defaultTab = getUrlParam(TAB_URL_PARAM) || Constants.PROSPECTUS_FILE_TABS.FILE_TABLES;


    if (fileData.fileTables && fileData.fileTables.length > 0) {

      let file_metadata_list: FileMetadataListItemProps[] = []
      for (const file_table of fileData.fileTables) {
        file_metadata_list.push({
          name: file_table.name,
          content: [{
            name: '',
            text: file_table.content,
            renderHTML: true
          }]
        })
      }

      // let file_metadata: FileMetadataListProps = {file_metadata: file_metadata_list}

      tabInfo.push({
        content: (
          <FileMetadataList file_metadata={file_metadata_list} />
        ),
        key: Constants.PROSPECTUS_FILE_TABS.FILE_TABLES,
        title: `File Tables (${fileData.fileTables.length})`,
      });
    }

    if (fileData.prospectusWaterfallSchemes && fileData.prospectusWaterfallSchemes.length > 0) {

      let file_metadata_list: FileMetadataListItemProps[] = [];
      for (const prospectus_waterfall_scheme of fileData.prospectusWaterfallSchemes) {
        let content: FileMetadataListItemContentProps[] = [];
        for (const scheme of prospectus_waterfall_scheme.scheme) {
          content.push({
            name: scheme.shortName,
            text: scheme.details,
            renderHTML: false
          });
        }

        file_metadata_list.push({
          name: prospectus_waterfall_scheme.name,
          content: content
        })
      }

      tabInfo.push({
        content: (
          <FileMetadataList file_metadata={file_metadata_list} />
        ),
        key: Constants.PROSPECTUS_FILE_TABS.PROSPECTUS_WATERFALL_SCHEMES,
        title: `Waterfall Schemes (${fileData.prospectusWaterfallSchemes.length})`,
      });
    }

    return (
      <TabsComponent
        tabs={tabInfo}
        defaultTab={defaultTab}
        onSelect={(key) => {
          setUrlParam(TAB_URL_PARAM, key);
          logAction({
            command: 'click',
            target_id: 'dashboard_page_tab',
            label: key,
          });
        }}
      />
    );
  }

  render() {
    const { isLoading, statusCode, fileData } = this.props;
    const { currentTab, isRightPanelOpen } =
      this.state;
    let innerContent: React.ReactNode;

    // We want to avoid rendering the previous table's metadata before new data is fetched in componentDidMount
    if (isLoading || !this.didComponentMount) {
      innerContent = <LoadingSpinner />;
    } else if (statusCode === STATUS_CODES.INTERNAL_SERVER_ERROR) {
      innerContent = <ErrorMessage />;
    } else {

      // const ownersEditText = fileData.sources[0]
      //   ? // TODO rename getDescriptionSourceDisplayName to more generic since
      //     // owners also edited on the same file?
      //     `${Constants.EDIT_OWNERS_TEXT} ${getDescriptionSourceDisplayName(
      //       fileData.sources[0].source_type
      //     )}`
      //   : '';
      // const editUrl = fileData.sources[0] ? fileData.sources[0].source : '';
      const ownersEditText = '';
      const editUrl = '';

      innerContent = (
        <div className="resource-detail-layout table-detail">
          <header className="resource-header">
            <div className="header-section">
              <Breadcrumb />
              <span
                className={
                  'icon icon-header ' +
                  getSourceIconClass(fileData.name, ResourceType.file)
                }
              />
            </div>
            <div className="header-section header-title">
              <h1
                className="header-title-text truncated"
                title={`${fileData.name}`}
              >
                {fileData.name}
              </h1>
              <BookmarkIcon
                bookmarkKey={fileData.key}
                resourceType={ResourceType.file}
              />
              <div className="header-details">
                <FileHeaderBullets
                  fileData={fileData}
                />
              </div>
              <div className="header-details">
              </div>
            </div>
          </header>
          <div className="single-column-layout">
            <aside className="left-panel">
              <EditableSection
                title={Constants.DESCRIPTION_TITLE}
                readOnly={!fileData.is_editable}
                editText={undefined}
                editUrl={undefined}
              >
                {
                <FileDescEditableText
                  maxLength={getMaxLength('fileDescLength')}
                  value={fileData.description}
                  editable={fileData.is_editable}
                />
                 }
                <span>
                  {notificationsEnabled() && (
                    <RequestDescriptionText
                      requestMetadataType={
                        RequestMetadataType.TABLE_DESCRIPTION
                      }
                    />
                  )}
                </span>
              </EditableSection>
              {issueTrackingEnabled() && (
                <section className="metadata-section">
                  {/*
                  <TableIssues
                    tableKey={this.key}
                    tableName={this.getDisplayName()}
                  />
                */}
                </section>
              )}
              <section className="two-column-layout">
                <section className="left-column">
                  <section className="metadata-section">
                    <div className="section-title">
                      File Path
                    </div>
                    {fileData.path}
                  </section>
                  {fileData.dataChannel &&  (
                    <section className="metadata-section">
                    <div className="section-title">
                        License
                      </div>
                      {fileData.dataChannel.license}
                    </section>
                  )}
                </section>
                <section className="right-column">
                  <EditableSection
                      title={Constants.OWNERS_TITLE}
                      readOnly={!fileData.is_editable}
                      editText={ownersEditText}
                      editUrl={editUrl || undefined}
                    >
                    <FileOwnerEditor resourceType={ResourceType.file} />
                  </EditableSection>
                </section>
              </section>
              <EditableSection title={Constants.TAG_TITLE}>
                <TagInput
                  resourceType={ResourceType.file}
                  uriKey={fileData.key}
                />
              </EditableSection>
            </aside>
            <main className="main-content-panel">
              {fileData.type == "pdf" && fileData.category == 'prospectus' &&
                this.renderProspectusTabs()
              }
            </main>
          </div>
        </div>
      );
    }

    return (
      <DocumentTitle
        title={`${this.getDisplayName()} - File Details`}
      >
        {innerContent}
      </DocumentTitle>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.fileMetadata.isLoading,
  statusCode: state.fileMetadata.statusCode,
  fileData: state.fileMetadata.fileData,
  fileOwners: state.fileMetadata.fileOwners,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getFileData,
      openRequestDescriptionDialog,
      searchDataLocation: (dataLocationType: string, dataLocationName: string) =>
        updateSearchState({
          filters: {
            [ResourceType.file]: { dataLocationType: { value: dataLocationType }, dataLocationName: { value: dataLocationName } },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<PropsFromState, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(FilePage);
