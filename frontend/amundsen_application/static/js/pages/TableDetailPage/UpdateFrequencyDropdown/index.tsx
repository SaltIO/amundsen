// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { Dropdown } from 'react-bootstrap';

import './styles.scss';

export interface UpdateFrequencyDropdownProps {
	updateFrequency?: string | null;
}

const UpdateFrequencyDropdown: React.FC<UpdateFrequencyDropdownProps> = ({
  updateFrequency,
}: UpdateFrequencyDropdownProps) => {

  return (
    <Dropdown
      className="header-link sources-dropdown"
      id="sources-dropdown"
    >
      <Dropdown.Toggle className="sources-dropdown-button">
        Update frequency
      </Dropdown.Toggle>
      <Dropdown.Menu className="sources-dropdown-menu">
        {['daily', 'weekly', 'monthly', 'quarterly', 'annually'].map(freq => (
          <Dropdown.Item as="button" key={freq} eventKey={freq} active={updateFrequency === freq}>
            {freq.charAt(0).toUpperCase() + freq.slice(1)}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default UpdateFrequencyDropdown;

