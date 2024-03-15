import {
  FileMetadata,
  Tag,
  OwnerDict
} from 'interfaces';

import {
  GetFileData,
  GetFileDataRequest,
  GetFileDataResponse,
  GetFileDescription,
  GetFileDescriptionRequest,
  GetFileDescriptionResponse,
  UpdateFileDescription,
  UpdateFileDescriptionRequest,
  UpdateFileOwner,
} from './types';

import fileOwnersReducer, {
  initialOwnersState,
  FileOwnerReducerState,
} from './owners/reducer';

import { STATUS_CODES } from '../../constants';

export const initialFileDataState: FileMetadata = {
  badges: [],
  key: '',
  name: '',
  description: '',
  path: '',
  type: '',
  category: '',
  is_editable: true
};

export const initialState: FileMetadataReducerState = {
  isLoading: true,
  statusCode: null,
  fileData: initialFileDataState,
  fileOwners: initialOwnersState,
};

/* ACTIONS */
export function getFileData(
  key: string,
  searchIndex?: string,
  source?: string
): GetFileDataRequest {
  return {
    payload: {
      key,
      searchIndex,
      source,
    },
    type: GetFileData.REQUEST,
  };
}
export function getFileDataFailure(): GetFileDataResponse {
  return {
    type: GetFileData.FAILURE,
    payload: {
      statusCode: STATUS_CODES.INTERNAL_SERVER_ERROR,
      data: initialFileDataState,
      owners: {},
      tags: [],
    },
  };
}
export function getFileDataSuccess(
  statusCode: number,
  data: FileMetadata,
  owners: OwnerDict,
  tags: Tag[]
): GetFileDataResponse {
  return {
    type: GetFileData.SUCCESS,
    payload: {
      statusCode,
      data,
      owners,
      tags,
    },
  };
}

export function getFileDescription(
  onSuccess?: () => any,
  onFailure?: () => any
): GetFileDescriptionRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
    },
    type: GetFileDescription.REQUEST,
  };
}
export function getFileDescriptionFailure(
  fileMetadata: FileMetadata
): GetFileDescriptionResponse {
  return {
    type: GetFileDescription.FAILURE,
    payload: {
      fileMetadata,
    },
  };
}
export function getFileDescriptionSuccess(
  fileMetadata: FileMetadata
): GetFileDescriptionResponse {
  return {
    type: GetFileDescription.SUCCESS,
    payload: {
      fileMetadata,
    },
  };
}

export function updateFileDescription(
  newValue: string,
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateFileDescriptionRequest {
  return {
    payload: {
      newValue,
      onSuccess,
      onFailure,
    },
    type: UpdateFileDescription.REQUEST,
  };
}

/* REDUCER */
export interface FileMetadataReducerState {
  dashboards?: {
    isLoading: boolean;
    errorMessage?: string;
  };
  isLoading: boolean;
  statusCode: number | null;
  fileData: FileMetadata;
  fileOwners: FileOwnerReducerState;
}

export default function reducer(
  state: FileMetadataReducerState = initialState,
  action
): FileMetadataReducerState {
  switch (action.type) {
    case GetFileData.REQUEST:
      return initialState;
    case GetFileData.FAILURE:
      return {
        ...state,
        isLoading: false,
        statusCode: (<GetFileDataResponse>action).payload.statusCode,
        fileData: initialFileDataState,
        fileOwners: fileOwnersReducer(state.fileOwners, action),
      };
    case GetFileData.SUCCESS:
      return {
        ...state,
        isLoading: false,
        statusCode: (<GetFileDataResponse>action).payload.statusCode,
        fileData: (<GetFileDataResponse>action).payload.data,
        fileOwners: fileOwnersReducer(state.fileOwners, action),
      };
    case GetFileDescription.FAILURE:
    case GetFileDescription.SUCCESS:
      return {
        ...state,
        fileData: (<GetFileDescriptionResponse>action).payload.fileMetadata,
      };
    case UpdateFileOwner.REQUEST:
    case UpdateFileOwner.FAILURE:
    case UpdateFileOwner.SUCCESS:
      return {
        ...state,
        fileOwners: fileOwnersReducer(state.fileOwners, action),
      };
    default:
      return state;
  }
}
