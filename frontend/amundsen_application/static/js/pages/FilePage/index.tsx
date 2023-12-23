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
import { getTableColumnLineage, getTableLineage } from 'ducks/lineage/reducer';
import { getNotices } from 'ducks/notices';
import { openRequestDescriptionDialog } from 'ducks/notification/reducer';
import { updateSearchState } from 'ducks/search/reducer';
import { GetFileDataRequest } from 'ducks/fileMetadata/types';
import {
  GetTableColumnLineageRequest,
  GetTableLineageRequest,
} from 'ducks/lineage/types';
import { OpenRequestAction } from 'ducks/notification/types';
import { GetNoticesRequest } from 'ducks/notices/types';
import { UpdateSearchStateRequest } from 'ducks/search/types';

import {
  getDescriptionSourceDisplayName,
  getMaxLength,
  getSourceIconClass,
  getResourceNotices,
  getDynamicNoticesEnabledByResource,
  getTableSortCriterias,
  issueTrackingEnabled,
  isTableListLineageEnabled,
  isColumnListLineageEnabled,
  notificationsEnabled,
  isTableQualityCheckEnabled,
  getTableLineageDefaultDepth,
} from 'config/config-utils';
import { NoticeType, NoticeSeverity } from 'config/config-types';

import BadgeList from 'features/BadgeList';
import ColumnList from 'features/ColumnList';
import ColumnDetailsPanel from 'features/ColumnList/ColumnDetailsPanel';

import { AlertList } from 'components/Alert';
import BookmarkIcon from 'components/Bookmark/BookmarkIcon';
import Breadcrumb from 'features/Breadcrumb';
import EditableSection from 'components/EditableSection';
import EditableText from 'components/EditableText';
import TabsComponent, { TabInfo } from 'components/TabsComponent';
import { TAB_URL_PARAM } from 'components/TabsComponent/constants';
import TagInput from 'features/Tags/TagInput';
import LoadingSpinner from 'components/LoadingSpinner';

import { logAction, logClick } from 'utils/analytics';
import { formatDateTimeShort } from 'utils/date';
import {
  buildTableKey,
  getLoggingParams,
  getUrlParam,
  setUrlParam,
  TablePageParams,
} from 'utils/navigation';

import {
  ProgrammaticDescription,
  ResourceType,
  TableMetadata,
  RequestMetadataType,
  SortCriteria,
  Lineage,
  TableApp,
  DynamicResourceNotice,
} from 'interfaces';
import { FormattedDataType } from 'interfaces/ColumnList';

import LineageButton from '../TableDetailPage/LineageButton';
import LineageLink from '../TableDetailPage/LineageLink';
import LineageList from '../TableDetailPage/LineageList';
import TableDescEditableText from '../TableDetailPage/TableDescEditableText';
import TableHeaderBullets from '../TableDetailPage/TableHeaderBullets';
import TableIssues from '../TableDetailPage/TableIssues';
import RequestDescriptionText from '../TableDetailPage/RequestDescriptionText';
import RequestMetadataForm from '../TableDetailPage/RequestMetadataForm';
import ListSortingDropdown from '../TableDetailPage/ListSortingDropdown';

import * as Constants from './constants';
import { STATUS_CODES } from '../../constants';

import './styles.scss';

const DASHBOARDS_PER_PAGE = 10;
const TABLE_SOURCE = 'table_page';
const SORT_CRITERIAS = {
  ...getTableSortCriterias(),
};
const SEVERITY_TO_NOTICE_SEVERITY = {
  0: NoticeSeverity.INFO,
  1: NoticeSeverity.WARNING,
  2: NoticeSeverity.ALERT,
};

/**
 * Merges the dynamic and static notices, doing a type matching for dynamic ones
 * @param data            Table metadata
 * @param notices         Dynamic notices
 * @returns NoticeType[]  Aggregated notices
 */
const aggregateResourceNotices = (
  data: TableMetadata,
  notices: DynamicResourceNotice[]
): NoticeType[] => {
  const staticNotice = getResourceNotices(
    ResourceType.table,
    `${data.cluster}.${data.database}.${data.schema}.${data.name}`
  );
  const dynamicNotices: NoticeType[] = notices.map((notice) => ({
    severity: SEVERITY_TO_NOTICE_SEVERITY[notice.severity],
    messageHtml: notice.message,
    payload: notice.payload,
  }));

  return staticNotice ? [...dynamicNotices, staticNotice] : dynamicNotices;
};

export interface PropsFromState {
  isLoading: boolean;
  statusCode: number | null;
  tableData: TableMetadata;
  tableLineage: Lineage;
  isLoadingLineage: boolean;
  notices: DynamicResourceNotice[];
  isLoadingNotices: boolean;
}
export interface DispatchFromProps {
  getFileData: (
    key: string,
    searchIndex?: string,
    source?: string
  ) => GetFileDataRequest;
  getTableLineageDispatch: (
    key: string,
    depth: number
  ) => GetTableLineageRequest;
  getNoticesDispatch: (key: string) => GetNoticesRequest;
  getColumnLineageDispatch: (
    key: string,
    columnName: string
  ) => GetTableColumnLineageRequest;
  openRequestDescriptionDialog: (
    requestMetadataType: RequestMetadataType,
    columnName: string
  ) => OpenRequestAction;
  searchSchema: (schemaText: string) => UpdateSearchStateRequest;
}

export interface MatchProps {
  cluster: string;
  database: string;
  schema: string;
  table: string;
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
  areNestedColumnsExpanded: boolean | undefined;
  sortedBy: SortCriteria;
  currentTab: string;
  isRightPanelOpen: boolean;
  isRightPanelPreExpanded: boolean;
  isExpandCollapseAllBtnVisible: boolean;
  selectedColumnKey: string;
  selectedColumnDetails?: FormattedDataType;
}

export class FilePage extends React.Component<
  FileProps & RouteComponentProps<any>,
  StateProps
> {
  private key: string;

  private didComponentMount: boolean = false;

  state = {
    areNestedColumnsExpanded: undefined,
    sortedBy: SORT_CRITERIAS.sort_order,
    currentTab: this.getDefaultTab(),
    isRightPanelOpen: false,
    isRightPanelPreExpanded: false,
    isExpandCollapseAllBtnVisible: true,
    selectedColumnKey: '',
    selectedColumnDetails: undefined,
  };

  componentDidMount() {
    const defaultDepth = getTableLineageDefaultDepth();
    const {
      location,
      getFileData,
      getTableLineageDispatch,
      getNoticesDispatch,
    } = this.props;
    const { index, source } = getLoggingParams(location.search);
    const {
      match: { params },
    } = this.props;

    this.key = buildTableKey(params);
    getFileData(this.key, index, source);

    if (isTableListLineageEnabled()) {
      getTableLineageDispatch(this.key, defaultDepth);
    }

    if (getDynamicNoticesEnabledByResource(ResourceType.table)) {
      getNoticesDispatch(this.key);
    }

    document.addEventListener('keydown', this.handleEscKey);
    window.addEventListener(
      'resize',
      this.handleExpandCollapseAllBtnVisibility
    );
    this.didComponentMount = true;
  }

  componentDidUpdate() {
    const defaultDepth = getTableLineageDefaultDepth();
    const {
      location,
      getFileData,
      getTableLineageDispatch,
      match: { params },
    } = this.props;
    const newKey = buildTableKey(params);

    if (this.key !== newKey) {
      const { index, source } = getLoggingParams(location.search);

      this.key = newKey;
      getFileData(this.key, index, source);

      if (isTableListLineageEnabled()) {
        getTableLineageDispatch(this.key, defaultDepth);
      }

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
    return getUrlParam(TAB_URL_PARAM) || Constants.FILE_TABS.TABLE;
  }

  getDisplayName() {
    const { match } = this.props;
    const { params } = match;

    return `${params.schema}.${params.table}`;
  }

  handleClick = (e) => {
    const { match, searchSchema } = this.props;
    const { params } = match;
    const schemaText = params.schema;

    logClick(e, {
      target_type: 'schema',
      label: schemaText,
    });
    searchSchema(schemaText);
  };

  renderProgrammaticDesc = (
    descriptions: ProgrammaticDescription[] | undefined
  ) => {
    if (!descriptions) {
      return null;
    }

    return descriptions.map((d) => (
      <EditableSection key={`prog_desc:${d.source}`} title={d.source} readOnly>
        <EditableText
          maxLength={999999}
          value={d.text}
          editable={false}
          allowDangerousHtml
        />
      </EditableSection>
    ));
  };

  toggleExpandingColumns = () => {
    const { areNestedColumnsExpanded } = this.state;
    const newValue =
      areNestedColumnsExpanded !== undefined
        ? !areNestedColumnsExpanded
        : false;

    this.setState({ areNestedColumnsExpanded: newValue });
  };

  handleSortingChange = (sortValue) => {
    this.toggleSort(SORT_CRITERIAS[sortValue]);
  };

  toggleSort = (sorting: SortCriteria) => {
    const { sortedBy } = this.state;

    if (sorting !== sortedBy) {
      this.setState({
        sortedBy: sorting,
      });
    }
  };

  preExpandRightPanel = (columnDetails: FormattedDataType) => {
    const { isRightPanelPreExpanded } = this.state;
    const { getColumnLineageDispatch } = this.props;

    if (isRightPanelPreExpanded) {
      return;
    }

    let key = '';

    if (columnDetails) {
      ({ key } = columnDetails);
      if (isColumnListLineageEnabled() && !columnDetails.isNestedColumn) {
        const { name, tableParams } = columnDetails;

        getColumnLineageDispatch(buildTableKey(tableParams), name);
      }
    }

    if (!isRightPanelPreExpanded && key) {
      this.setState({
        isRightPanelOpen: true,
        isRightPanelPreExpanded: true,
        selectedColumnKey: key,
        selectedColumnDetails: columnDetails,
      });
    }
  };

  toggleRightPanel = (newColumnDetails: FormattedDataType | undefined) => {
    const { isRightPanelOpen, selectedColumnKey } = this.state;
    const { getColumnLineageDispatch } = this.props;

    let key = '';

    if (newColumnDetails) {
      ({ key } = newColumnDetails);
    }

    const shouldPanelOpen =
      (key && key !== selectedColumnKey) || !isRightPanelOpen;

    if (
      isColumnListLineageEnabled() &&
      shouldPanelOpen &&
      newColumnDetails &&
      !newColumnDetails.isNestedColumn
    ) {
      const { name, tableParams } = newColumnDetails;

      getColumnLineageDispatch(buildTableKey(tableParams), name);
    }

    if (newColumnDetails && shouldPanelOpen) {
      logAction({
        command: 'click',
        label: `${newColumnDetails.key} ${newColumnDetails.type.type}`,
        target_id: `column::${newColumnDetails.key}`,
        target_type: 'column stats',
      });
    }

    this.setState({
      isRightPanelOpen: shouldPanelOpen,
      selectedColumnKey: shouldPanelOpen ? key : '',
      selectedColumnDetails: newColumnDetails,
    });
  };

  hasColumnsToExpand = () => {
    const { tableData } = this.props;

    return tableData.columns.some((col) => col.type_metadata?.children?.length);
  };

  renderTabs(editText: string, editUrl: string | null) {
    const tabInfo: TabInfo[] = [];
    const {
      tableData,
      isLoadingLineage,
      tableLineage,
    } = this.props;
    const {
      areNestedColumnsExpanded,
      sortedBy,
      currentTab,
      isRightPanelOpen,
      selectedColumnKey,
    } = this.state;
    const tableParams: TablePageParams = {
      cluster: tableData.cluster,
      database: tableData.database,
      table: tableData.name,
      schema: tableData.schema,
    };
    const selectedColumn = getUrlParam(Constants.COLUMN_URL_KEY);

    return (
      <TabsComponent
        tabs={tabInfo}
        defaultTab={currentTab}
        onSelect={(key) => {
          if (isRightPanelOpen) {
            this.toggleRightPanel(undefined);
          }
          this.setState({ currentTab: key });
          setUrlParam(TAB_URL_PARAM, key);
          logAction({
            command: 'click',
            target_id: 'table_detail_tab',
            label: key,
          });
        }}
        isRightPanelOpen={isRightPanelOpen}
      />
    );
  }

  renderColumnTabActionButtons(isRightPanelOpen, sortedBy) {
    const { areNestedColumnsExpanded, isExpandCollapseAllBtnVisible } =
      this.state;

    return (
      <div
        className={`column-tab-action-buttons ${
          isRightPanelOpen ? 'has-open-right-panel' : 'has-closed-right-panel'
        }`}
      >
        {isExpandCollapseAllBtnVisible && this.hasColumnsToExpand() && (
          <button
            className="btn btn-link expand-collapse-all-button"
            type="button"
            onClick={this.toggleExpandingColumns}
          >
            <h3 className="expand-collapse-all-text">
              {areNestedColumnsExpanded ||
              areNestedColumnsExpanded === undefined
                ? Constants.COLLAPSE_ALL_NESTED_LABEL
                : Constants.EXPAND_ALL_NESTED_LABEL}
            </h3>
          </button>
        )}
        {!isRightPanelOpen && (
          <ListSortingDropdown
            options={SORT_CRITERIAS}
            currentSelection={sortedBy}
            onChange={this.handleSortingChange}
          />
        )}
      </div>
    );
  }
  
  render() {
    const { isLoading, statusCode, tableData, notices } = this.props;
    const { sortedBy, currentTab, isRightPanelOpen, selectedColumnDetails } =
      this.state;
    let innerContent: React.ReactNode;

    // console.log("DREW: isLoading="+isLoading)
    // console.log("DREW: statusCode="+statusCode)
    // console.log("DREW: tableData="+tableData)

    // We want to avoid rendering the previous table's metadata before new data is fetched in componentDidMount
    if (isLoading || !this.didComponentMount) {
      innerContent = <LoadingSpinner />;
    } else if (statusCode === STATUS_CODES.INTERNAL_SERVER_ERROR) {
      innerContent = <ErrorMessage />;
    } else {
      const data = tableData;
      const editText = data.sources[0]
        ? `${Constants.EDIT_DESC_TEXT} ${getDescriptionSourceDisplayName(
            data.sources[0].source_type
          )}`
        : '';
      const ownersEditText = data.sources[0]
        ? // TODO rename getDescriptionSourceDisplayName to more generic since
          // owners also edited on the same file?
          `${Constants.EDIT_OWNERS_TEXT} ${getDescriptionSourceDisplayName(
            data.sources[0].source_type
          )}`
        : '';
      const editUrl = data.sources[0] ? data.sources[0].source : '';
      const aggregatedTableNotices = aggregateResourceNotices(data, notices);

      innerContent = (
        <div className="resource-detail-layout table-detail">
          {notificationsEnabled() && <RequestMetadataForm />}
          <header className="resource-header">
            <div className="header-section">
              <Breadcrumb />
              <span
                className={
                  'icon icon-header ' +
                  getSourceIconClass(data.database, ResourceType.table)
                }
              />
            </div>
            <div className="header-section header-title">
              <h1
                className="header-title-text truncated"
                title={`${data.schema}.${data.name}`}
              >
                <Link to="/search" onClick={this.handleClick}>
                  {data.schema}
                </Link>
                .{data.name}
              </h1>
              <BookmarkIcon
                bookmarkKey={data.key}
                resourceType={ResourceType.table}
              />
              <div className="header-details">
                <TableHeaderBullets
                  database={data.database}
                  cluster={data.cluster}
                  isView={data.is_view}
                />
              </div>
              <div className="header-details">
                {data.badges.length > 0 && <BadgeList badges={data.badges} />}
              </div>
            </div>
            <div className="header-section header-links header-external-links">
              <LineageLink tableData={data} />
            </div>
            <div className="header-section header-buttons">
              <LineageButton tableData={data} />
            </div>
          </header>
          <div className="single-column-layout">
            <aside className="left-panel">
              <AlertList notices={aggregatedTableNotices} />
              <EditableSection
                title={Constants.DESCRIPTION_TITLE}
                readOnly={!data.is_editable}
                editText={editText}
                editUrl={editUrl || undefined}
              >
                <TableDescEditableText
                  maxLength={getMaxLength('tableDescLength')}
                  value={data.description}
                  editable={data.is_editable}
                />
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
                  <TableIssues
                    tableKey={this.key}
                    tableName={this.getDisplayName()}
                  />
                </section>
              )}
              <section className="two-column-layout">
                <section className="left-column">
                  <section className="metadata-section">
                    <div className="section-title">
                      {Constants.LAST_UPDATED_TITLE}
                    </div>
                    <time className="time-body-text">
                      {  
                        data.last_updated_timestamp != null
                        ? formatDateTimeShort({
                            epochTimestamp: data.last_updated_timestamp,
                          })
                        : ''
                      }
                    </time>
                  </section>
                  <section className="metadata-section">
                    <div className="section-title">
                      {Constants.DATE_RANGE_TITLE}
                    </div>
                  </section>
                  {this.renderProgrammaticDesc(
                    data.programmatic_descriptions.left
                  )}
                </section>
                <section className="right-column">
                  <EditableSection
                    title={Constants.OWNERS_TITLE}
                    readOnly={!data.is_editable}
                    editText={ownersEditText}
                    editUrl={editUrl || undefined}
                  >
                  </EditableSection>
                  <section className="metadata-section">
                    <div className="section-title">
                      {Constants.FREQ_USERS_TITLE}
                    </div>
                  </section>
                  {this.renderProgrammaticDesc(
                    data.programmatic_descriptions.right
                  )}
                </section>
              </section>
              <EditableSection title={Constants.TAG_TITLE}>
                <TagInput
                  resourceType={ResourceType.table}
                  uriKey={tableData.key}
                />
              </EditableSection>
              {this.renderProgrammaticDesc(
                data.programmatic_descriptions.other
              )}
            </aside>
            <main className="main-content-panel">              
            </main>
            {isRightPanelOpen && selectedColumnDetails && (
              <ColumnDetailsPanel
                columnDetails={selectedColumnDetails!}
                togglePanel={this.toggleRightPanel}
              />
            )}
          </div>
        </div>
      );
    }

    return (
      <DocumentTitle
        title={`${this.getDisplayName()} - Amundsen Table Details`}
      >
        {innerContent}
      </DocumentTitle>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.tableMetadata.isLoading,
  statusCode: state.tableMetadata.statusCode,
  tableData: state.tableMetadata.tableData,
  tableLineage: state.lineage.lineageTree,
  isLoadingLineage: state.lineage ? state.lineage.isLoading : true,
  notices: state.notices.notices,
  isLoadingNotices: state.notices ? state.notices.isLoading : false,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getFileData,
      getTableLineageDispatch: getTableLineage,
      getNoticesDispatch: getNotices,
      getColumnLineageDispatch: getTableColumnLineage,
      openRequestDescriptionDialog,
      searchSchema: (schemaText: string) =>
        updateSearchState({
          filters: {
            [ResourceType.table]: { schema: { value: schemaText } },
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
