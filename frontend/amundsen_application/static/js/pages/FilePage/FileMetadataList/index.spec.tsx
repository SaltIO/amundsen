// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import FileMetadataList, { FileMetadataListProps } from '.';
import FileMetadataListItem from '../FileMetadataListItem';

const setup = (propOverrides?: Partial<FileMetadataListProps>) => {
  const props = {
    file_metadata: [],
    ...propOverrides,
  };
  const wrapper = shallow<FileMetadataList>(<FileMetadataList {...props} />);

  return { props, wrapper };
};

describe('FileMetadataList', () => {
  describe('render', () => {
    it('returns a list item for each filemetadata', () => {
      const { props, wrapper } = setup({
        file_metadata: [
          {
            name: 'TEST',
            content: [{
              name: 'TEST',
              text: 'TEST',
              renderHTML: false
            }]
          },
        ],
      });
      const expected = props.file_metadata.length;
      const actual = wrapper.find(FileMetadataListItem).length;

      expect(actual).toEqual(expected);
    });

    describe('when no filemetadata available', () => {
      it('returns null', () => {
        const { wrapper } = setup();
        const expected = 0;
        const actual = wrapper.find(FileMetadataListItem).length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
