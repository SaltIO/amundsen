// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { updateTableUpdateFrequency } from 'ducks/tableMetadata/reducer';

import EditableSelect, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableSelect';

export const mapStateToProps = (state: GlobalState) => {
  return {
    refreshValue: state.tableMetadata.tableData.update_frequency,
    options: ['daily', 'weekly', 'monthly', 'quarterly', 'annually'],
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ onSubmitValue: updateTableUpdateFrequency }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(EditableSelect);


