// This file should be used to add new config variables or overwrite defaults from config-default.ts

import { AppConfigCustom } from './config-types';
import { CustomBadgeStyle } from './config-types-custom';
import { FilterType, ResourceType, SortDirection } from '../interfaces';

const configCustom: AppConfigCustom = {
  badges: {
    marts: {
      style: CustomBadgeStyle.MARTS,
      displayName: 'Marts',
    },
    wrangling: {
      style: CustomBadgeStyle.WRANGLING,
      displayName: 'Wrangling',
    },
    staging: {
      style: CustomBadgeStyle.STAGING,
      displayName: 'Staging',
    },
    landing: {
      style: CustomBadgeStyle.LANDING,
      displayName: 'Landing',
    },
    snowflake: {
      style: CustomBadgeStyle.SNOWFLAKE,
      displayName: 'Snowflake',
    },
    mysql: {
      style: CustomBadgeStyle.MYSQL,
      displayName: 'MySQL',
    },
    mssql: {
      style: CustomBadgeStyle.MSSQL,
      displayName: 'MSSQL',
    },
    dbt: {
      style: CustomBadgeStyle.DBT,
      displayName: 'dbt',
    },
    watermark: {
      style: CustomBadgeStyle.WATERMARK,
      displayName: 'Watermark',
    },
    primarykey: {
      style: CustomBadgeStyle.PRIMARY_KEY,
      displayName: 'Primary Key',
    },
    foreignkey: {
      style: CustomBadgeStyle.FOREIGN_KEY,
      displayName: 'Foreign Key',
    },
    unique: {
      style: CustomBadgeStyle.UNIQUE,
      displayName: 'Unique',
    }
  },
  browse: {
    curatedTags: [],
    showAllTags: true,
    showBadgesInHome: false,
    hideNonClickableBadges: false,
  },
  mailClientFeatures: {
    feedbackEnabled: true,
    notificationsEnabled: true,
  },
  indexDashboards: {
    enabled: false,
  },
  indexUsers: {
    enabled: true,    // Enables User Profile within Amundsen Frontend
  },
  indexFeatures: {
    enabled: false,
  },
  userIdLabel: 'email address',
  issueTracking: {
    enabled: true,
    issueDescriptionTemplate: '',
    projectSelection: {
      enabled: false,
      title: 'Issue project key (optional)',
      inputHint: '',
    },
  },
  announcements: {
    enabled: true,
  },
  featureLineage: {
    inAppListEnabled: true,
  },
  navLinks: [
    {
      label: 'Announcements',
      id: 'nav::announcements',
      href: '/announcements',
      use_router: true,
    },
    {
      label: 'Browse',
      id: 'nav::browse',
      href: '/browse',
      use_router: true,
    },
  ],
  eagleye: {
    isEnabled: false
  },
  tableLineage: {
    defaultLineageDepth: 25,
    inAppListEnabled: true,
    inAppPageEnabled: true,
    externalEnabled: false,
    iconPath: 'PATH_TO_ICON',
    isBeta: false,
    urlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string
    ) =>
      `https://DEFAULT_LINEAGE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}`,
  },
  fileLineage: {
    defaultLineageDepth: 25,
    inAppListEnabled: true,
    inAppPageEnabled: true,
    externalEnabled: false,
    iconPath: 'PATH_TO_ICON',
    isBeta: false,
    urlGenerator: (
      data_location_type: string,
      data_location_name: string,
      data_location_container: string,
      type: string,
      name: string
    ) =>
      `https://DEFAULT_LINEAGE_URL?data_location_type=${data_location_type}&data_location_name=${data_location_name}&data_location_container=${data_location_container}&type=${type}&name=${name}`,
  },
  columnLineage: {
    inAppListEnabled: true,
    inAppPageEnabled: true,
    urlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string,
      column: string
    ) =>
      `https://DEFAULT_LINEAGE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}&column=${column}`,
  },
  tableProfile: {
    isBeta: true,
    isExploreEnabled: false,
    exploreUrlGenerator: (
      database: string,
      cluster: string,
      schema: string,
      table: string,
      partitionKey?: string,
      partitionValue?: string
    ) =>
      `https://DEFAULT_EXPLORE_URL?schema=${schema}&cluster=${cluster}&db=${database}&table=${table}`,
  },
  tableQualityChecks: {
    isEnabled: true,
  },
  nestedColumns: {
    maxNestedColumns: 500,
  },
  searchPagination: {
    resultsPerPage: 10,
  },
  documentTitle: 'CMD+RVL - Data Discovery Platform',
  footerContentHtml: '<span style="font-family: \'PPMori\';font-weight: 700">Data Discovery Platform</span><span style="font-family: \'PPMori\';font-weight: 400"> Powered by </span><a style="font-family: \'PPMori\';font-weight: 700" href="https://cmdrvl.com" target="_blank" rel="noopener noreferrer">CMD+RVL</a>',
};

export default configCustom;
