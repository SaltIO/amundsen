import { testSaga } from 'redux-saga-test-plan';

import { OwnerDict, UpdateMethod, UpdateOwnerPayload } from 'interfaces';

import globalState from 'fixtures/globalState';

import * as API from '../api/v0';
import { STATUS_CODES } from '../../../constants';

import reducer, {
  updateFileOwner,
  updateFileOwnerFailure,
  updateFileOwnerSuccess,
  initialOwnersState,
  FileOwnerReducerState,
} from './reducer';
import {
  getFileData,
  getFileDataFailure,
  getFileDataSuccess,
} from '../reducer';

import { updateFileOwnerWorker, updateFileOwnerWatcher } from './sagas';

import { UpdateFileOwner } from '../types';

jest.spyOn(API, 'generateOwnerUpdateRequests').mockImplementation(() => []);

describe('fileMetadata:owners ducks', () => {
  let expectedOwners: OwnerDict;
  let updatePayload: UpdateOwnerPayload[];
  let mockSuccess;
  let mockFailure;

  beforeAll(() => {
    expectedOwners = {
      testId: {
        display_name: 'test',
        profile_url: 'test.io',
        email: 'test@test.com',
        user_id: 'testId',
      },
    };
    updatePayload = [{ method: UpdateMethod.PUT, id: 'testId' }];
    mockSuccess = jest.fn();
    mockFailure = jest.fn();
  });

  describe('actions', () => {
    it('updateFileOwner - returns the action to update file owners', () => {
      const action = updateFileOwner(updatePayload, mockSuccess, mockFailure);
      const { payload } = action;

      expect(action.type).toBe(UpdateFileOwner.REQUEST);
      expect(payload.updateArray).toBe(updatePayload);
      expect(payload.onSuccess).toBe(mockSuccess);
      expect(payload.onFailure).toBe(mockFailure);
    });

    it('updateFileOwnerFailure - returns the action to process failure', () => {
      const action = updateFileOwnerFailure(expectedOwners);
      const { payload } = action;

      expect(action.type).toBe(UpdateFileOwner.FAILURE);
      expect(payload.owners).toBe(expectedOwners);
    });

    it('updateFileOwnerSuccess - returns the action to process success', () => {
      const action = updateFileOwnerSuccess(expectedOwners);
      const { payload } = action;

      expect(action.type).toBe(UpdateFileOwner.SUCCESS);
      expect(payload.owners).toBe(expectedOwners);
    });
  });

  describe('reducer', () => {
    let testState: FileOwnerReducerState;

    beforeAll(() => {
      testState = initialOwnersState;
    });

    it('should return the existing state if action is not handled', () => {
      expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
    });

    it('should handle UpdateFileOwner.REQUEST', () => {
      expect(
        reducer(
          testState,
          updateFileOwner(updatePayload, mockSuccess, mockFailure)
        )
      ).toEqual({
        ...testState,
        isLoading: true,
      });
    });

    it('should handle UpdateFileOwner.FAILURE', () => {
      expect(
        reducer(testState, updateFileOwnerFailure(expectedOwners))
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });

    it('should handle UpdateFileOwner.SUCCESS', () => {
      expect(
        reducer(testState, updateFileOwnerSuccess(expectedOwners))
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });

    it('should handle GetFileData.REQUEST', () => {
      expect(reducer(testState, getFileData('testKey'))).toEqual({
        ...testState,
        isLoading: true,
        owners: {},
      });
    });

    it('should handle GetFileData.FAILURE', () => {
      const action = getFileDataFailure();

      expect(reducer(testState, action)).toEqual({
        ...testState,
        isLoading: false,
        owners: action.payload.owners,
      });
    });

    it('should handle GetFileData.SUCCESS', () => {
      const mockFileData = globalState.fileMetadata.fileData;

      expect(
        reducer(
          testState,
          getFileDataSuccess(
            STATUS_CODES.OK,
            mockFileData,
            expectedOwners,
            []
          )
        )
      ).toEqual({
        ...testState,
        isLoading: false,
        owners: expectedOwners,
      });
    });
  });

  describe('sagas', () => {
    describe('updateFileOwnerWatcher', () => {
      it('takes every UpdateFileOwner.REQUEST with updateFileOwnerWorker', () => {
        testSaga(updateFileOwnerWatcher)
          .next()
          .takeEvery(UpdateFileOwner.REQUEST, updateFileOwnerWorker);
      });
    });

    describe('updateFileOwnerWorker', () => {
      describe('executes flow for updating owners and returning up to date owner dict', () => {
        let sagaTest;

        beforeAll(() => {
          sagaTest = (action) =>
            testSaga(updateFileOwnerWorker, action)
              .next()
              .select()
              .next(globalState)
              .all(
                API.generateOwnerUpdateRequests(
                  updatePayload,
                  globalState.fileMetadata.fileData
                )
              )
              .next()
              .call(API.getFileOwners, globalState.fileMetadata.fileData.key)
              .next(expectedOwners)
              .put(updateFileOwnerSuccess(expectedOwners));
        });

        it('without success callback', () => {
          sagaTest(updateFileOwner(updatePayload)).next().isDone();
        });

        it('with success callback', () => {
          sagaTest(updateFileOwner(updatePayload, mockSuccess, mockFailure))
            .next()
            .call(mockSuccess)
            .next()
            .isDone();
        });
      });

      describe('handles request error', () => {
        let sagaTest;

        beforeAll(() => {
          sagaTest = (action) =>
            testSaga(updateFileOwnerWorker, action)
              .next()
              .select()
              .next(globalState)
              .throw(new Error())
              .put(
                updateFileOwnerFailure(
                  globalState.fileMetadata.fileOwners.owners
                )
              );
        });

        it('without failure callback', () => {
          sagaTest(updateFileOwner(updatePayload)).next().isDone();
        });

        it('with failure callback', () => {
          sagaTest(updateFileOwner(updatePayload, mockSuccess, mockFailure))
            .next()
            .call(mockFailure)
            .next()
            .isDone();
        });
      });
    });
  });
});
