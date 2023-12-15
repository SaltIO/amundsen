// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Dropdown } from 'react-bootstrap';

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
  maxLength?: number;
  value?: string | null;
  allowDangerousHtml?: boolean;
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
  readonly textAreaRef: React.RefObject<HTMLTextAreaElement>;
  readonly aiTextAreaRef: React.RefObject<HTMLTextAreaElement>;

  public static defaultProps: UpdateFrequencyEditorProps = {
    isLoading: false,
    editable: true,
    maxLength: 500,
    value: '',
  };

  constructor(props: UpdateFrequencyEditorProps) {
    super(props);
    this.textAreaRef = React.createRef<HTMLTextAreaElement>();
    this.aiTextAreaRef = React.createRef<HTMLTextAreaElement>();

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

    // console.log(`refreshValue=${refreshValue}`)
    // console.log(`stateValue=${stateValue}`)
    // console.log(`propValue=${propValue}`)
    // console.log(`prevProps.value=${prevProps.value}`)

    if (prevProps.value !== propValue) {
      this.setState({ value: propValue });
    }
    else if (isEditing && !prevProps.isEditing) {
    }
    else if ((refreshValue || stateValue) &&
              refreshValue !== stateValue &&
              !isDisabled) {
      // disable the component if a refresh is needed
      //this.setState({ isDisabled: true });
    }
  }

  handleExitEditMode = (e: React.MouseEvent<HTMLButtonElement>) => {
    logClick(e, {
      label: 'Cancel Editable Text',
    });
    this.exitEditMode();
  };

  exitEditMode = () => {
    const { setEditMode } = this.props;

    setEditMode?.(false);
  };

  handleEnterEditMode = (e: React.MouseEvent<HTMLButtonElement>) => {
    const { setEditMode } = this.props;

    logClick(e, {
      label: 'Add Editable Text',
    });
    setEditMode?.(true);
  };

  handleRefreshText = (e: React.MouseEvent<HTMLButtonElement>) => {
    const { refreshValue } = this.props;
    const textArea = this.textAreaRef.current;

    //this.setState({ value: refreshValue, isDisabled: false });
    logClick(e, {
      label: 'Refresh Editable Text',
    });

    //if (textArea && refreshValue) {
    //  textArea.value = refreshValue;
    //  autosize.update(textArea);
    //}
  };

  handleUpdateText = (e: React.MouseEvent<HTMLButtonElement>) => {
    const { setEditMode, onSubmitValue } = this.props;
    const newValue = this.textAreaRef.current?.value;

    const onSuccessCallback = () => {
      setEditMode?.(false);
      this.setState({ value: newValue });
    };
    const onFailureCallback = () => {
      this.exitEditMode();
    };

    logClick(e, {
      label: 'Update Editable Text',
    });

    if (newValue) {
      onSubmitValue?.(newValue, onSuccessCallback, onFailureCallback);
    }
  };

  render() {
    const { isEditing, editable, maxLength, allowDangerousHtml } = this.props;
    const { value = '', isDisabled } = this.state;
    const updateFrequency = 'daily';

    return (
      <Dropdown
        className="header-link sources-dropdown"
        id="sources-dropdown"
      >
        <Dropdown.Toggle className="sources-dropdown-button">
          Update frequency
        </Dropdown.Toggle>
        <Dropdown.Menu className="sources-dropdown-menu">
        <Dropdown.Item as="button"
        {updateFrequency === 'daily' ? 'active' : ''}
        >Daily</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency === 'weekly' ? 'active' : ''}
        >Weekly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency === 'monthly' ? 'active' : ''}
        >Monthly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency === 'quarterly' ? 'active' : ''}
        >Quarterly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency === 'annually' ? 'active' : ''}
        >Annually</Dropdown.Item>
      </Dropdown.Menu>
      </Dropdown>
    )
  }
}

export default UpdateFrequencyEditor;

