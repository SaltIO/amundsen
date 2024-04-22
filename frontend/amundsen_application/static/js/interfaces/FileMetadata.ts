// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { Badge } from './Badges';
import { Tag } from './Tags';
import { User } from './User';
import { DataLocation, FilesystemDataLocation, AwsS3DataLocation } from './DataLocation';
import { DataChannel } from './DataChannel';



export interface FileTable {
  name: string
  content: string
}

export interface ProspectusScheme {
  shortName: string
  details: string
}

export interface ProspectusWaterfallScheme {
  name: string
  scheme: ProspectusScheme[]
}

export interface FileMetadata {
  badges: Badge[];
  key: string;
  name: string;
  description?: string;
  type: string;
  category?: string;
  path: string;
  dataLocation?: FilesystemDataLocation | AwsS3DataLocation | DataLocation;
  dataChannel?: DataChannel;
  tags?:  Tag[];
  fileTables?: FileTable[]
  prospectusWaterfallSchemes?: ProspectusWaterfallScheme[];
  is_editable: boolean;
}

export interface FileOwners {
  isLoading: boolean;
  owners: User[];
}
