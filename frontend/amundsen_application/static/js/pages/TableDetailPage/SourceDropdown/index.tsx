// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Dropdown } from 'react-bootstrap';

import AvatarLabel from 'components/AvatarLabel';
import { TableSource } from 'interfaces';
import { logClick } from 'utils/analytics';
import GithubMenu from './GithubMenu';
import AWSS3Menu from './AWSS3Menu';
import GenericMenu from './GenericMenu';
import {
  SOURCES_LABEL,
  GITHUB,
  AWSS3,
  SNOWFLAKE,
  GITHUB_LOGO_PATH,
  AWSS3_LOGO_PATH,
  SNOWFLAKE_LOGO_PATH,
  DATABASE_LOGO_PATH,
  SOURCE
} from './constants';
import './styles.scss';

export interface SourceDropdownProps {
  tableSources: TableSource[];
}

const getImagePath = (tableSourceType) => {
  switch (tableSourceType) {
    case GITHUB.toLowerCase():
      return GITHUB_LOGO_PATH;
    case AWSS3.toLowerCase():
      return AWSS3_LOGO_PATH;
    case SNOWFLAKE.toLowerCase():
      return SNOWFLAKE_LOGO_PATH;
    default:
      return DATABASE_LOGO_PATH;
  }
};

const isAirflowOrDatabricksApp = (appName) =>
  appName.toLowerCase() === AIRFLOW.toLowerCase() ||
  appName.toLowerCase() === DATABRICKS.toLowerCase();

const sortByNameOrId = (a, b) =>
  a.name.localeCompare(b.name) || a.id.localeCompare(b.id);

const hasSameNameAndKind = (app, name, kind) =>
  // Checks if the app matches the given name and kind
  // If its kind is empty, check if the given kind is the default Producing value
  app.name === name &&
  ((app.kind && app.kind === kind) || (!app.kind && kind === PRODUCING));

const getSortedSourceTypes = (sources: TableSource[]) => {
  // Sort app kinds by Producing then Consuming if they exist in the list, and then all others following
  // If no kind is specified, default to Producing
  const sourceTypes: string[] = [
    ...new Set(sources.map((source) => (source.source_type ? source.source_type : SOURCE))),
  ];

  const producingKind = appKinds.filter(
    (kind) => kind.toLowerCase() === PRODUCING
  );
  const consumingKind = appKinds.filter(
    (kind) => kind.toLowerCase() === CONSUMING
  );
  const remainingKinds = appKinds.filter(
    (kind) =>
      kind.toLowerCase() !== PRODUCING && kind.toLowerCase() !== CONSUMING
  );

  return [...producingKind, ...consumingKind, ...remainingKinds];
};

const handleClick = (event) => {
  event.stopPropagation();
  logClick(event);
};

const getDropdownMenuContents = (tableSources) => {
  return (
    <GenericMenu
      tableSources={tableSources}
      getSortedSourceTypes={getSortedSourceTypes}
      hasSameNameAndKind={hasSameNameAndKind}
      handleClick={handleClick}
    />
  );
};

const SourceDropdown: React.FC<SourceDropdownProps> = ({
  tableSources,
}: SourceDropdownProps) => {
  if (tableSources === null || tableSources.length === 0) {
    return null;
  }

  tableSources.sort(sortByNameOrId);

  const image = DATABASE_LOGO_PATH;
  const avatarLabel = SOURCES_LABEL;

  return (
    <Dropdown
      className="header-link sources-dropdown"
      id="application-dropdown"
      pullRight
    >
      <Dropdown.Toggle className="sources-dropdown-button">
        <AvatarLabel
          label={avatarLabel}
          src={image}
          round="true"
        />
      </Dropdown.Toggle>
      <Dropdown.Menu className="sources-dropdown-menu">
        {getDropdownMenuContents(tableSources)}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default SourceDropdown;
