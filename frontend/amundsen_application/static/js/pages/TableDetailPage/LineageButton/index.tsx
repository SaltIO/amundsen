// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import { TableMetadata } from 'interfaces';
import { isTableLineagePageEnabled } from 'config/config-utils';
import { buildTableLineageURL } from 'utils/navigation';
import AvatarLabel from 'components/AvatarLabel';

export interface LineageButtonProps {
  tableData: TableMetadata;
}

const BUTTON_LABEL = 'Lineage';
// const BUTTON_BADGE = 'beta';
const BUTTON_IMAGE = '/static/images/lineage.png';

const LineageButton: React.FC<LineageButtonProps> = ({
  tableData,
}: LineageButtonProps) => {
  if (!isTableLineagePageEnabled()) return null;
  const path = buildTableLineageURL(tableData);

  return (
    // <Link to={path} className="btn btn-default btn-lg">
    //   {BUTTON_LABEL}
    //   <span className="static-badge flag label label-warning">
    //     <div className="badge-overlay-primary">{BUTTON_BADGE}</div>
    //   </span>
    // </Link>

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
