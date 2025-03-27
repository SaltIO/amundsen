import { SagaIterator } from 'redux-saga';
import { all, call, put, select, takeEvery } from 'redux-saga/effects';

import * as API from '../api/v0';

import { updateFileOwnerFailure, updateFileOwnerSuccess } from './reducer';

import { UpdateFileOwner, UpdateFileOwnerRequest } from '../types';

export function* updateFileOwnerWorker(
  action: UpdateFileOwnerRequest
): SagaIterator {
  const { payload } = action;
  const state = yield select();
  const { fileData } = state.fileMetadata;

  try {
    const requestList = API.generateOwnerUpdateRequests(
      payload.updateArray,
      fileData
    );

    yield all(requestList);
    const newOwners = yield call(API.getFileOwners, fileData.key);

    yield put(updateFileOwnerSuccess(newOwners));
    if (payload.onSuccess) {
      yield call(payload.onSuccess);
    }
  } catch (e) {
    yield put(updateFileOwnerFailure(state.fileMetadata.fileOwners.owners));
    if (payload.onFailure) {
      yield call(payload.onFailure);
    }
  }
}
export function* updateFileOwnerWatcher(): SagaIterator {
  yield takeEvery(UpdateFileOwner.REQUEST, updateFileOwnerWorker);
}
