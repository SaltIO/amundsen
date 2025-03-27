// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { mount } from 'enzyme';

import FileMetadataListItem, { FileMetadataListItemProps } from '.';

const setup = (propOverrides?: Partial<FileMetadataListItemProps>) => {
  const props: FileMetadataListItemProps = {
    name: 'Mode',
    content: [{
      name: 'testFileMetadata',
      text: 'test',
      renderHTML: false
    }],
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount(<FileMetadataListItem {...props} />);

  return { props, wrapper };
};

describe('FileMetadataListItem', () => {
  describe('render', () => {
    it('should render without errors', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render one filemetadata list item', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.filemetadata-list-item').length;

      expect(actual).toEqual(expected);
    });

    it('should render the filemetadata name', () => {
      const { wrapper, props } = setup();
      const expected = props.name;
      const actual = wrapper.find('.filemetadata-list-item-name').text();

      expect(actual).toEqual(expected);
    });

    it('should not render the expanded content', () => {
      const { wrapper } = setup();
      const expected = 0;
      const actual = wrapper.find('.filemetadata-list-expanded-content').length;

      expect(actual).toEqual(expected);
    });

    describe('when item is expanded', () => {
      let wrapper;

      beforeAll(() => {
        ({ wrapper } = setup());

        wrapper.find('.filemetadata-list-header').simulate('click');
      });

      it('should show the filemetadata label', () => {
        const expected = 1;
        const actual = wrapper.find('.filemetadata-list-filemetadata-label').length;

        expect(actual).toEqual(expected);
      });

      it('should show the filemetadata content', () => {
        const expected = 1;
        const actual = wrapper.find('.filemetadata-list-filemetadata-content').length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifetime', () => {
    describe('when clicked on the item', () => {
      it('should render the expanded content', () => {
        const { wrapper } = setup();
        const expected = 1;

        wrapper.find('.filemetadata-list-header').simulate('click');
        const actual = wrapper.find('.filemetadata-list-expanded-content').length;

        expect(actual).toEqual(expected);
      });

      describe('when clicking again', () => {
        it('should hide the expanded content', () => {
          const { wrapper } = setup();
          const expected = 0;

          wrapper.find('.filemetadata-list-header').simulate('click');
          wrapper.find('.filemetadata-list-header').simulate('click');
          const actual = wrapper.find('.filemetadata-list-expanded-content').length;

          expect(actual).toEqual(expected);
        });
      });
    });
  });
});
