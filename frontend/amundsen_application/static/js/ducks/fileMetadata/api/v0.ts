import axios, { AxiosResponse, AxiosError } from 'axios';

import {
  FileMetadata,
  User,
  Tag,
  ResourceType,
  UpdateOwnerPayload,
} from 'interfaces';

/** HELPERS **/
import { createOwnerUpdatePayload, getOwnersDictFromUsers } from 'utils/owner';
import {
  getFileQueryParams,
  getFileDataFromResponseData,
  // shouldSendNotification,
  // createOwnerNotificationData,
} from './helpers';


const JSONBig = require('json-bigint');

export const API_PATH = '/api/metadata/v0';

type MessageAPI = { msg: string };

export type FileData = FileMetadata & {
  owners: User[];
  tags: Tag[];
};
export type DescriptionAPI = { description: string } & MessageAPI;
export type FileDataAPI = { fileData: FileData } & MessageAPI;

export function getFileData(key: string, index?: string, source?: string) {
  const fileQueryParams = getFileQueryParams({ key, index, source });
  const fileURL = `${API_PATH}/file?${fileQueryParams}`;
  const fileRequest = axios.get<FileDataAPI>(fileURL);

  return fileRequest.then((fileResponse: AxiosResponse<FileDataAPI>) => ({
    statusCode: fileResponse.status,
    data: getFileDataFromResponseData(fileResponse.data),
    owners: getOwnersDictFromUsers(fileResponse.data.fileData.owners),
    tags: fileResponse.data.fileData.tags,
  }));
}

export function getFileDescription(fileData: FileMetadata) {
  const fileParams = getFileQueryParams({ key: fileData.key });

  return axios
    .get(`${API_PATH}/get_file_description?${fileParams}`)
    .then((response: AxiosResponse<DescriptionAPI>) => {
      fileData.description = response.data.description;

      return fileData;
    });
}

export function updateFileDescription(
  description: string,
  fileData: FileMetadata
) {
  return axios.put(`${API_PATH}/put_file_description`, {
    description,
    key: fileData.key,
    source: 'user',
  });
}

export function getFileOwners(key: string) {
  const fileParams = getFileQueryParams({ key });

  return axios
    .get(`${API_PATH}/file?${fileParams}`)
    .then((response: AxiosResponse<FileDataAPI>) =>
      getOwnersDictFromUsers(response.data.fileData.owners)
    );
}

export function generateOwnerUpdateRequests(
  updateArray: UpdateOwnerPayload[],
  fileData: FileMetadata
): any {
  /* Return the list of requests to be executed */
  return updateArray.map((updateOwnerPayload) => {
    const updatePayload = createOwnerUpdatePayload(
      ResourceType.file,
      fileData.key,
      updateOwnerPayload
    );
    // const notificationData = createOwnerNotificationData(
    //   updateOwnerPayload,
    //   fileData
    // );

    /* Chain requests to send notification on success to desired users */
    return axios(updatePayload)
      .then(() =>
        axios.get(`/api/metadata/v0/user?user_id=${updateOwnerPayload.id}`)
      )
      .then((response) => {
        // if (shouldSendNotification(response.data.user)) {
        //   return axios.post('/api/mail/v0/notification', notificationData);
        // }
      });
  });
}


