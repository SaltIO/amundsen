// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { Dropdown, MenuItem, OverlayTrigger, Popover } from 'react-bootstrap';

import { logClick } from 'utils/analytics';

import {
  SOURCES_LABEL,
  DATABASE_LOGO_PATH,
  DELAY_SHOW_POPOVER_MS,
  SOURCE_TYPE_TO_NAME,
  SOURCE_TYPE_TO_IMAGE,
} from './constants';

import './styles.scss';

export interface UpdateFrequencyDropdownProps {
  updateFrequency: string;
}

const UpdateFrequencyDropdown: React.FC<UpdateFrequencyDropdownProps> = ({
  updateFrequency,
}: UpdateFrequencyDropdownProps) => {
  //if (updateFrequency === null) {
  //  return null;
  //}

  return (
    <Dropdown
      className="header-link sources-dropdown"
      id="sources-dropdown"
    >
      <Dropdown.Toggle className="sources-dropdown-button">
        Choose update frequency
      </Dropdown.Toggle>
      <Dropdown.Menu className="sources-dropdown-menu">
        <Dropdown.Item as="button">Daily</Dropdown.Item>
        <Dropdown.Item as="button">Weekly</Dropdown.Item>
        <Dropdown.Item as="button">Monthly</Dropdown.Item>
        <Dropdown.Item as="button">Quarterly</Dropdown.Item>
        <Dropdown.Item as="button">Annually</Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default SourceDropdown;