// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { DefaultBadgeStyle } from 'config/config-types';
import Flag, { FlagProps } from '.';

describe('Flag', () => {
  let props: FlagProps;
  let subject;

  beforeEach(() => {
    props = {
      text: 'Testing',
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    subject = shallow(<Flag {...props} />);
  });

  describe('render', () => {
    it('renders span with correct default className', () => {
      expect(subject.find('span').props().className).toEqual(
        `flag label label-${DefaultBadgeStyle.DEFAULT}`
      );
    });

    it('renders span with correct custom className', () => {
      props.labelStyle = DefaultBadgeStyle.PRIMARY;
      subject.setProps(props);

      expect(subject.find('span').props().className).toEqual(
        `flag label label-${DefaultBadgeStyle.PRIMARY}`
      );
    });

    it('renders span with correct text', () => {
      expect(subject.find('span').text()).toEqual(props.text);
    });
  });
});
