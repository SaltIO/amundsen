// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { Dropdown, MenuItem, OverlayTrigger, Popover } from 'react-bootstrap';

import { logClick } from 'utils/analytics';

import './styles.scss';

export interface UpdateFrequencyDropdownProps {
	updateFrequency?: string | null;
}

const UpdateFrequencyDropdown: React.FC<UpdateFrequencyDropdownProps> = ({
  updateFrequency,
}: UpdateFrequencyDropdownProps) => {

  const handleSelect = (event) => {
    event.stopPropagation();
    logClick(event);
    console.log('Choice!!!')
    console.log(event);
  };

  return (
    <Dropdown
      className="header-link sources-dropdown"
      id="sources-dropdown"
    >
      <Dropdown.Toggle className="sources-dropdown-button">
        Update frequency
      </Dropdown.Toggle>
      <Dropdown.Menu className="sources-dropdown-menu" onSelect={handleSelect}>
        <Dropdown.Item as="button"
        {updateFrequency == 'daily' ? 'active' : ''}
        >Daily</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency == 'weekly' ? 'active' : ''}
        >Weekly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency == 'monthly' ? 'active' : ''}
        >Monthly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency == 'quarterly' ? 'active' : ''}
        >Quarterly</Dropdown.Item>
        <Dropdown.Item as="button"
        {updateFrequency == 'annually' ? 'active' : ''}
        >Annually</Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default UpdateFrequencyDropdown;