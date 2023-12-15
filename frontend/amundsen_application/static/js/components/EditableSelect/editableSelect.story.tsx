// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';

import StorySection from '../StorySection';
import EditableSelect from '.';

export default {
  title: 'Components/EditableSelect'
};

export const SelectBox = () => (
  <>
    <StorySection title="with default Weekly">
      <EditableSelect value={'weekly'}
                      options={['daily', 'weekly', 'monthly', 'quarterly', 'annually']}
                      editable={true} />
    </StorySection>
    <StorySection title="with custom list">
      <EditableSelect value={'a'}
                      options={['a', 'b', 'c', 'd']}
                      editable={true} />
    </StorySection>
    <StorySection title="with no value specified">
      <EditableSelect options={['daily', 'weekly', 'monthly', 'quarterly', 'annually']}
                      editable={true} />
    </StorySection>
    <StorySection title="not editable">
      <EditableSelect value={'weekly'}
                      options={['daily', 'weekly', 'monthly', 'quarterly', 'annually']}
                      editable={false} />
    </StorySection>
  </>
);

SelectBox.storyName = 'Select Box';