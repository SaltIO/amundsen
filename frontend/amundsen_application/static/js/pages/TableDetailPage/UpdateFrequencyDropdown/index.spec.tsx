// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Dropdown, MenuItem } from 'react-bootstrap';
import { mount } from 'enzyme';

import UpdateFrequencyDropdown, { UpdateFrequencyDropdownProps } from '.';


const setup = (propOverrides?: Partial<UpdateFrequencyDropdownProps>) => {
  const props = {
    updateFrequency: 'Daily',
    ...propOverrides,
  };
  const wrapper = mount<typeof UpdateFrequencyDropdown>(
    <UpdateFrequencyDropdown {...props} />
  );

  return { props, wrapper };
};

describe('UpdateFrequencyDropdown', () => {
  describe('render', () => {
    it('renders without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    describe('when no options are passed', () => {
      it('does not render the component', () => {
        const { wrapper } = setup();
        const expected = 0;
        const actual = wrapper.find('.source-dropdown').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when one option is passed', () => {
      it('renders a Dropdown component', () => {
        const { wrapper } = setup({
          updateFrequency: 'Daily',
        });
        const expected = 1;
        const actual = wrapper.find(Dropdown).length;

        expect(actual).toEqual(expected);
      });

      it('renders a MenuItem component', () => {
        const { wrapper } = setup({
          updateFrequency: 'Daily',
        });
        const expected = 1;
        const actual = wrapper.find(MenuItem).length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
