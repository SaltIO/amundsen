import {
  AnalyticsEvent,
  FileMetadata,
  Tag,
  OwnerDict,
  UpdateOwnerPayload,
} from 'interfaces';

export enum GetFileData {
  REQUEST = 'amundsen/fileMetadata/GET_FILE_DATA_REQUEST',
  SUCCESS = 'amundsen/fileMetadata/GET_FILE_DATA_SUCCESS',
  FAILURE = 'amundsen/fileMetadata/GET_FILE_DATA_FAILURE',
}
export interface GetFileDataRequest {
  type: GetFileData.REQUEST;
  payload: {
    key: string;
    searchIndex?: string;
    source?: string;
  };
}
export interface GetFileDataResponse {
  type: GetFileData.SUCCESS | GetFileData.FAILURE;
  payload: {
    statusCode: number | null;
    data: FileMetadata;
    owners: OwnerDict;
    tags: Tag[];
  };
}

export enum GetFileDescription {
  REQUEST = 'amundsen/fileMetadata/GET_FILE_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/fileMetadata/GET_FILE_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/fileMetadata/GET_FILE_DESCRIPTION_FAILURE',
}
export interface GetFileDescriptionRequest {
  type: GetFileDescription.REQUEST;
  payload: {
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface GetFileDescriptionResponse {
  type: GetFileDescription.SUCCESS | GetFileDescription.FAILURE;
  payload: {
    fileMetadata: FileMetadata;
  };
}

export enum UpdateFileDescription {
  REQUEST = 'amundsen/fileMetadata/UPDATE_FILE_DESCRIPTION_REQUEST',
  SUCCESS = 'amundsen/fileMetadata/UPDATE_FILE_DESCRIPTION_SUCCESS',
  FAILURE = 'amundsen/fileMetadata/UPDATE_FILE_DESCRIPTION_FAILURE',
}
export interface UpdateFileDescriptionRequest {
  type: UpdateFileDescription.REQUEST;
  payload: {
    newValue: string;
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface UpdateFileDescriptionResponse {
  type: UpdateFileDescription.SUCCESS | UpdateFileDescription.FAILURE;
}

export enum UpdateFileOwner {
  REQUEST = 'amundsen/fileMetadata/UPDATE_FILE_OWNER_REQUEST',
  SUCCESS = 'amundsen/fileMetadata/UPDATE_FILE_OWNER_SUCCESS',
  FAILURE = 'amundsen/fileMetadata/UPDATE_FILE_OWNER_FAILURE',
}
export interface UpdateFileOwnerRequest {
  type: UpdateFileOwner.REQUEST;
  payload: {
    updateArray: UpdateOwnerPayload[];
    onSuccess?: () => any;
    onFailure?: () => any;
  };
}
export interface UpdateFileOwnerResponse {
  type: UpdateFileOwner.SUCCESS | UpdateFileOwner.FAILURE;
  payload: {
    owners: OwnerDict;
  };
}
