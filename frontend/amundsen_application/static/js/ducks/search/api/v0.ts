import axios, { AxiosResponse } from 'axios';

import {
  indexDashboardsEnabled,
  indexFeaturesEnabled,
  indexUsersEnabled,
  indexFilesEnabled,
  indexProvidersEnabled,
  searchHighlightingEnabled,
} from 'config/config-utils';
import { ResourceType, SearchType } from 'interfaces';

import {
  DashboardSearchResults,
  FeatureSearchResults,
  TableSearchResults,
  UserSearchResults,
  FileSearchResults,
  DataProviderSearchResults,
} from '../types';

import { ResourceFilterReducerState } from '../filters/reducer';

export const BASE_URL = '/api/search/v1';

const RESOURCE_TYPES = ['dashboard', 'feature', 'table', 'user', 'file', 'data_provider'];

export interface SearchAPI {
  msg: string;
  status_code: number;
  search_term: string;
  dashboard?: DashboardSearchResults;
  feature?: FeatureSearchResults;
  table?: TableSearchResults;
  user?: UserSearchResults;
  file?: FileSearchResults;
  data_provider?: DataProviderSearchResults;
}

export const searchHelper = (response: AxiosResponse<SearchAPI>) => {
  const { data } = response;
  const ret = { searchTerm: data.search_term };

  RESOURCE_TYPES.forEach((key) => {
    if (data[key]) {
      ret[key] = data[key];
    }
  });

  return ret;
};

export const isResourceIndexed = (resource: ResourceType) => {
  // table is always configured
  if (resource === ResourceType.table) {
    return true;
  }
  if (resource === ResourceType.user) {
    return indexUsersEnabled();
  }
  if (resource === ResourceType.dashboard) {
    return indexDashboardsEnabled();
  }
  if (resource === ResourceType.feature) {
    return indexFeaturesEnabled();
  }
  if (resource === ResourceType.file) {
    return indexFilesEnabled();
  }
  if (resource === ResourceType.data_provider) {
    return indexProvidersEnabled();
  }

  return false;
};

export function search(
  pageIndex: number,
  resultsPerPage: number,
  resources: ResourceType[],
  searchTerm: string,
  filters: ResourceFilterReducerState = {},
  searchType: SearchType
) {
  console.log('search()');
  console.log(resources);
  // If given invalid resource in list dont search for that one only for valid ones
  const validResources = resources.filter((r) => isResourceIndexed(r));

  console.log('validResources');
  console.log(validResources);
  if (!validResources.length) {
    // If there are no resources to search through then return {}
    return Promise.resolve({});
  }

  console.log('highlightingOptions');
  const highlightingOptions = validResources.reduce(
    (obj, resource) => ({
      ...obj,
      [resource]: {
        enable_highlight: searchHighlightingEnabled(resource),
      },
    }),
    {}
  );

  console.log('make the call!');
  return axios
    .post(`${BASE_URL}/search`, {
      filters,
      pageIndex,
      resources: validResources,
      resultsPerPage,
      searchTerm,
      searchType,
      highlightingOptions,
    })
    .then(searchHelper);
}
