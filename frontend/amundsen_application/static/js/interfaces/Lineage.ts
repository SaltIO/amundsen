import { Badge } from './Badges';

export interface TableLineageItemDetail {
  name: string;
  schema: string;
  cluster: string;
  database: string;
}

export interface FileLineageItemDetail {
  name: string;
  type: string;
  data_location_type: string;
  data_location_container: string;
  data_location_name: string;
}

export interface LineageItem {
  key: string;
  type: string;
  badges: Badge[];
  level: number;
  parent: string | null;
  usage: number | null;
  source?: string;
  link?: string;
  in_amundsen?: boolean;
  lineage_item_detail: TableLineageItemDetail | FileLineageItemDetail;
}

export interface Lineage {
  key?: string;
  direction?: string;
  depth?: number;
  downstream_entities: LineageItem[];
  upstream_entities: LineageItem[];
  downstream_count?: number;
  upstream_count?: number;
}

export interface TableLineageParams {
  key: string;
  direction: string;
  depth: number;
}

export interface ColumnLineageParams {
  key: string;
  direction: string;
  depth: number;
  column: string;
}

// To keep the backward compatibility for the list based lineage
// ToDo: Please remove once list based view is deprecated
export interface ColumnLineageMap {
  [columnName: string]: {
    lineageTree: Lineage;
    isLoading: boolean;
  };
}
