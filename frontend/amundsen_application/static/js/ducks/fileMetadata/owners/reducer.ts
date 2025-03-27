import { OwnerDict, UpdateOwnerPayload } from 'interfaces';

import {
  GetFileData,
  GetFileDataResponse,
  UpdateFileOwner,
  UpdateFileOwnerRequest,
  UpdateFileOwnerResponse,
} from '../types';

/* ACTIONS */
export function updateFileOwner(
  updateArray: UpdateOwnerPayload[],
  onSuccess?: () => any,
  onFailure?: () => any
): UpdateFileOwnerRequest {
  return {
    payload: {
      onSuccess,
      onFailure,
      updateArray,
    },
    type: UpdateFileOwner.REQUEST,
  };
}
export function updateFileOwnerFailure(
  owners: OwnerDict
): UpdateFileOwnerResponse {
  return {
    type: UpdateFileOwner.FAILURE,
    payload: {
      owners,
    },
  };
}
export function updateFileOwnerSuccess(
  owners: OwnerDict
): UpdateFileOwnerResponse {
  return {
    type: UpdateFileOwner.SUCCESS,
    payload: {
      owners,
    },
  };
}

/* REDUCER */
export interface FileOwnerReducerState {
  isLoading: boolean;
  owners: OwnerDict;
}

export const initialOwnersState: FileOwnerReducerState = {
  isLoading: true,
  owners: {},
};

export default function reducer(
  state: FileOwnerReducerState = initialOwnersState,
  action
): FileOwnerReducerState {
  switch (action.type) {
    case GetFileData.REQUEST:
      return { isLoading: true, owners: {} };
    case GetFileData.FAILURE:
    case GetFileData.SUCCESS:
      return {
        isLoading: false,
        owners: (<GetFileDataResponse>action).payload.owners,
      };
    case UpdateFileOwner.REQUEST:
      return { ...state, isLoading: true };
    case UpdateFileOwner.FAILURE:
    case UpdateFileOwner.SUCCESS:
      return {
        isLoading: false,
        owners: (<UpdateFileOwnerResponse>action).payload.owners,
      };
    default:
      return state;
  }
}
