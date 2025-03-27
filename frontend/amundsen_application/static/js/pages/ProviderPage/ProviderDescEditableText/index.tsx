
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  getProviderDescription,
  updateProviderDescription,
} from 'ducks/providerMetadata/reducer';
import {
  getGPTResponse
} from 'ducks/ai/reducer';

import EditableText, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/EditableText';

export const mapStateToProps = (state: GlobalState) => ({
  refreshValue: state.providerMetadata.providerData.description,
  gptResponse: state.gptResponse.gptResponse
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getLatestValue: getProviderDescription,
      onSubmitValue: updateProviderDescription,
      getGPTResponse: getGPTResponse
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(EditableText);
