import { AppConfig } from './config-types';
import configDefault from './config-default';
import configCustom from './config-custom';
import configHost from './config-host';
import { ResourceType } from '../interfaces';
import _ from 'lodash';

// This is not a shallow merge.
// Any defined members of customConfig will override configDefault.
// Any defined members of customHost will override configCustom.
// const appConfig: AppConfig = { ...configDefault, ...configCustom, ...configHost };

console.log("starting appconfig")

// Merge badges
const mergedBadges = _.merge(
    {},
    configDefault.badges,
    (configCustom.badges ? configCustom.badges : {}),
    (configHost.badges ? configHost.badges : {})
);

// Merge resourceConfig
const mergedResourceConfig = _.merge(
    {},
    configDefault.resourceConfig,
    configCustom.resourceConfig,
    configHost.resourceConfig
);


// Perform complete overrides for other properties
const appConfig: AppConfig = {
    ...configDefault,
    ...configCustom,
    ...configHost,
    badges: mergedBadges, // Use the merged result
    resourceConfig: mergedResourceConfig
};

// console.log("AppConfig");
// console.log(JSON.stringify(appConfig, null, 2));

export default appConfig;