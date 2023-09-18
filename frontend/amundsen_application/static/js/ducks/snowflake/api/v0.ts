import axios, { AxiosResponse } from 'axios';

import { SnowflakeTableShare } from 'interfaces';
import { API_PATH } from 'ducks/tableMetadata/api/v0';
import { sortSnowflakeTableSharesAlphabetical } from 'ducks/utilMethods';

export type SnowflakeTableSharesAPI = {
  msg: string;
  snowflake_table_shares: SnowflakeTableShare[];
};

export function getSnowflakeTableShares(tableUri: string) {
  return axios
  .get(`${API_PATH}/snowflake/get_snowflake_table_shares?tableUri=${encodeURIComponent(tableUri)}`)
    .then((response: AxiosResponse<SnowflakeTableSharesAPI>) =>
      response.data.snowflake_table_shares.sort(sortSnowflakeTableSharesAlphabetical)
    );
}