import * as qs from 'simple-query-string';

import { filterFromObj } from 'ducks/utilMethods';

import {
  NotificationType,
  PeopleUser,
  FileMetadata,
  UpdateMethod,
  UpdateOwnerPayload,
} from 'interfaces';
import * as API from './v0';

export interface FileQueryParams {
  key: string;
  index?: string;
  source?: string;
}

/**
 * Generates the query string parameters needed for requests that act on a particular file resource.
 */
export function getFileQueryParams(params: FileQueryParams): string {
  return qs.stringify(params);
}

/**
 * Parses the response for file metadata information to create a FileMetadata object
 */
export function getFileDataFromResponseData(
  responseData: API.FileDataAPI
): FileMetadata {
  return filterFromObj(responseData.fileData, [
    'owners',
    'tags',
  ]) as FileMetadata;
}

/**
 * Creates post data for sending a notification to owners when they are added/removed
 */
export function createOwnerNotificationData(
  payload: UpdateOwnerPayload,
  fileData: FileMetadata
) {
  return {
    notificationType:
      payload.method === UpdateMethod.PUT
        ? NotificationType.OWNER_ADDED
        : NotificationType.OWNER_REMOVED,
    options: {
      resource_name: `${fileData.type}.${fileData.name}`,
      // resource_path: `/file_detail/${fileData.dataLocation?.type}/${fileData.database}/${fileData.schema}/${fileData.name}`,
    },
    recipients: [payload.id],
  };
}

/**
 * Workaround logic for not sending emails to alumni or teams.
 */
export function shouldSendNotification(user: PeopleUser): boolean {
  return user.is_active && !!user.display_name;
}

