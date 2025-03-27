// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';

import { DefaultBadgeStyle } from 'config/config-types';
import { CaseType } from 'utils/text';
import StorySection from '../StorySection';
import Flag from '.';

export default {
  title: 'Components/Flags',
};

export const Flags = () => (
  <>
    <StorySection title="Lower Case Flag">
      <Flag caseType={CaseType.LOWER_CASE} text="Test Flag" />
    </StorySection>
    <StorySection title="Upper Case Flag">
      <Flag caseType={CaseType.UPPER_CASE} text="Test Flag" />
    </StorySection>
    <StorySection title="Sentence Case Flag">
      <Flag caseType={CaseType.SENTENCE_CASE} text="Test Flag" />
    </StorySection>
    <StorySection title="Default Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.DEFAULT}
      />
    </StorySection>
    <StorySection title="Primary Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.PRIMARY}
      />
    </StorySection>
    <StorySection title="Informational Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.INFO}
      />
    </StorySection>
    <StorySection title="Success Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.SUCCESS}
      />
    </StorySection>
    <StorySection title="Warning Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.WARNING}
      />
    </StorySection>
    <StorySection title="Danger Style Flag">
      <Flag
        caseType={CaseType.SENTENCE_CASE}
        text="Test Flag"
        labelStyle={DefaultBadgeStyle.DANGER}
      />
    </StorySection>
  </>
);

Flags.storyName = 'Flags';
