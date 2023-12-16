// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { EditableSectionChildProps } from 'components/EditableSection';

import { logClick } from 'utils/analytics';

export interface StateFromProps {
  refreshValue?: string;
  options: string[];
}

export interface DispatchFromProps {
  onSubmitValue?: (
    newValue: string,
    onSuccess?: () => any,
    onFailure?: () => any
  ) => void;
}

export interface ComponentProps {
  editable?: boolean;
  value?: string;
}

export type EditableSelectProps = ComponentProps &
  DispatchFromProps &
  StateFromProps &
  EditableSectionChildProps;

interface EditableSelectState {
  value?: string;
  isDisabled: boolean;
}

class EditableSelect extends React.Component<
  EditableSelectProps,
  EditableSelectState
> {
  public static defaultProps: EditableSelectProps = {
    editable: true,
    value: '',
    options: [''],
  };

  constructor(props: EditableSelectProps) {
    super(props);

    this.state = {
      isDisabled: false,
      value: props.value,
    };
  }

  componentDidUpdate(prevProps: EditableSelectProps) {
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
      //setEditMode?.(false);
      this.setState({ value: newValue });
    };
    const onFailureCallback = () => {
      //this.exitEditMode();
      console.log("select failed")
    };

    if (newValue) {
      onSubmitValue?.(newValue, onSuccessCallback, onFailureCallback);
    }
  };

  render() {
    const { isEditing, editable, options } = this.props;
    const { value = '', isDisabled } = this.state;

    return (
        <select
            value={value == null ? 'none' : value}
            onChange={e => this.setSelectValue(e.target.value)}
            id="update-table-frequency-dropdown"
            disabled={isDisabled || !editable} // If you want to control the disabled state of the dropdown
        >
            {options.map(option => (
                <option key={option} value={option.toLowerCase()}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                </option>
            ))}
        </select>
    );
  }
}

export default EditableSelect;

