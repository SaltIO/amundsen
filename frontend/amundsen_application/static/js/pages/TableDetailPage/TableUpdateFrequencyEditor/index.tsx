// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { updateTableUpdateFrequency } from 'ducks/tableMetadata/reducer';

import UpdateFrequencyEditor, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/UpdateFrequencyEditor';

export const mapStateToProps = (state: GlobalState) => {
  return {
    isLoading: state.tableMetadata.update_frequency.isLoading,
    refreshValue: state.tableMetadata.update_frequency.frequency,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ onSubmitValue: updateTableUpdateFrequency }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(UpdateFrequencyEditor);


