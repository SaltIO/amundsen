// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { EditableSectionChildProps } from 'components/EditableSection';

import { logClick } from 'utils/analytics';

export interface StateFromProps {
  isLoading: boolean;
  refreshValue?: string | null;
}

export interface DispatchFromProps {
  onSubmitValue?: (
    newValue: string,
    onSuccess?: () => any,
    onFailure?: () => any
  ) => void;
}

export interface ComponentProps {
  isLoading: false,
  editable?: boolean;
  value?: string | null;
}

export type UpdateFrequencyEditorProps = ComponentProps &
  DispatchFromProps &
  StateFromProps &
  EditableSectionChildProps;

interface UpdateFrequencyEditorState {
  value?: string | null;
  isDisabled: boolean;
}

class UpdateFrequencyEditor extends React.Component<
  UpdateFrequencyEditorProps,
  UpdateFrequencyEditorState
> {
  public static defaultProps: UpdateFrequencyEditorProps = {
    isLoading: false,
    editable: true,
    value: '',
  };

  constructor(props: UpdateFrequencyEditorProps) {
    super(props);

    this.state = {
      isDisabled: false,
      value: props.value,
    };
  }

  componentDidUpdate(prevProps: UpdateFrequencyEditorProps) {
    const { value: stateValue, isDisabled } = this.state;
    const {
      value: propValue,
      isEditing,
      refreshValue
    } = this.props;

    if (prevProps.value !== propValue) {
      this.setState({ value: propValue });
    }
    else if (isEditing && !prevProps.isEditing) {
    }
    else if ((refreshValue || stateValue) &&
              refreshValue !== stateValue &&
              !isDisabled) {
      // disable the component if a refresh is needed
      this.setState({ isDisabled: true });
    }
  }

  setSelectValue = (value) => {
    const { setEditMode, onSubmitValue } = this.props;
    const newValue = value;

    const onSuccessCallback = () => {
      setEditMode?.(false);
      this.setState({ value: newValue });
    };
    const onFailureCallback = () => {
      this.exitEditMode();
    };

    logClick(e, {
      label: 'Update Select',
    });

    if (newValue) {
      onSubmitValue?.(newValue, onSuccessCallback, onFailureCallback);
    }
  };

  render() {
    const { isEditing, editable } = this.props;
    const { value = '', isDisabled } = this.state;

    return (
        <select
            value={value}
            onChange={e => setSelectValue(e.target.value)}
            id="update-table-frequency-dropdown"
        >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="annually">Annually</option>
        </select>
    );
  }
}

export default UpdateFrequencyEditor;

