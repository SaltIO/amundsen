import { AppConfig } from './config-types';
import configDefault from './config-default';
import configCustom from './config-custom';
import configHost from './config-host';
import _ from 'lodash';

// This is not a shallow merge.
// Any defined members of customConfig will override configDefault.
// Any defined members of customHost will override configCustom.
// const appConfig: AppConfig = { ...configDefault, ...configCustom, ...configHost };

// Use _.merge specifically for the nestedConfig element
const mergedBadges = _.merge(
    {},
    configDefault.badges,
    configCustom.badges,
    configHost.badges
);

// Perform complete overrides for other properties
const appConfig: AppConfig = {
    ...configDefault,
    ...configCustom,
    ...configHost,
    badges: mergedBadges, // Use the merged result for nestedConfig
};

export default appConfig;