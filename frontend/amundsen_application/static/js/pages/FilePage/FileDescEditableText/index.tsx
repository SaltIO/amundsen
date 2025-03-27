
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  getFileDescription,
  updateFileDescription,
} from 'ducks/fileMetadata/reducer';
import {
  getGPTResponse
} from 'ducks/ai/reducer';

import EditableText, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableText';

export const mapStateToProps = (state: GlobalState) => ({
  refreshValue: state.fileMetadata.fileData.description,
  gptResponse: state.gptResponse.gptResponse
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getLatestValue: getFileDescription,
      onSubmitValue: updateFileDescription,
      getGPTResponse: getGPTResponse
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(EditableText);
