// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { updateFileOwner } from 'ducks/fileMetadata/owners/reducer';

import OwnerEditor, {
  ComponentProps,
  DispatchFromProps,
  StateFromProps,
} from 'components/OwnerEditor';

import { indexUsersEnabled } from 'config/config-utils';

export const mapStateToProps = (state: GlobalState) => {
  const ownerObj = state.fileMetadata.fileOwners.owners;
  const items = Object.keys(ownerObj).reduce((obj, ownerId) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { profile_url, user_id, display_name } = ownerObj[ownerId];
    let profileLink = profile_url;
    let isExternalLink = true;

    if (indexUsersEnabled()) {
      isExternalLink = false;
      profileLink = `/user/${user_id}?source=owned_by`;
    }

    obj[ownerId] = {
      label: display_name,
      link: profileLink,
      isExternal: isExternalLink,
    };

    return obj;
  }, {});

  return {
    isLoading: state.fileMetadata.fileOwners.isLoading,
    itemProps: items,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ onUpdateList: updateFileOwner }, dispatch);

export default connect<StateFromProps, DispatchFromProps, ComponentProps>(
  mapStateToProps,
  mapDispatchToProps
)(OwnerEditor);
