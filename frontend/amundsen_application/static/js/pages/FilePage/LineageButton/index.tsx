// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import { FileMetadata } from 'interfaces';
import { isFileLineagePageEnabled } from 'config/config-utils';
import { buildFileLineageURL } from 'utils/navigation';
import AvatarLabel from 'components/AvatarLabel';

export interface LineageButtonProps {
  fileData: FileMetadata;
}

const BUTTON_LABEL = 'Lineage';
// const BUTTON_BADGE = 'beta';
const BUTTON_IMAGE = '/static/images/lineage.png';

const LineageButton: React.FC<LineageButtonProps> = ({
  fileData,
}: LineageButtonProps) => {
  if (!isFileLineagePageEnabled()) return null;
  const path = buildFileLineageURL(fileData);

  return (
    <Link to={path} className="btn btn-default btn-lg">
      <AvatarLabel
        label={BUTTON_LABEL}
        src={BUTTON_IMAGE}
        round={true}
      />
    </Link>
  );
};

export default LineageButton;
