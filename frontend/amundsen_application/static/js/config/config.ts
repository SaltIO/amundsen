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

// Merge badges
const mergedBadges = _.merge(
    {},
    configDefault.badges,
    (configCustom.badges ? configCustom.badges : {}),
    (configHost.badges ? configHost.badges : {})
);

// Merge Table Supported Sources
const mergedTableSupportedSourcesConfig = _.merge(
    {},
    configDefault.resourceConfig[ResourceType.table].supportedSources,
    (configCustom.resourceConfig &&
     ResourceType.table in configCustom.resourceConfig &&
     configCustom?.resourceConfig[ResourceType.table]?.supportedSources ?
        configCustom.resourceConfig[ResourceType.table].supportedSources :
        {}
    ),
    (configHost.resourceConfig &&
     ResourceType.table in configHost.resourceConfig &&
     configHost.resourceConfig[ResourceType.table]?.supportedSources ?
        configHost.resourceConfig[ResourceType.table].supportedSources :
        {}
    )
);

// Merge Dashboard Supported Sources
const mergedDashboardSupportedSourcesConfig = _.merge(
    {},
    configDefault.resourceConfig[ResourceType.dashboard].supportedSources,
    (configCustom.resourceConfig &&
     ResourceType.dashboard in configCustom.resourceConfig &&
     configCustom.resourceConfig[ResourceType.dashboard]?.supportedSources ?
        configCustom.resourceConfig[ResourceType.dashboard].supportedSources :
        {}
    ),
    (configHost.resourceConfig &&
     ResourceType.dashboard in configHost.resourceConfig &&
     configHost.resourceConfig[ResourceType.dashboard]?.supportedSources ?
        configHost.resourceConfig[ResourceType.dashboard].supportedSources :
        {}
    )
);

// Merge Data Provider Supported Sources
const mergedDataProviderSupportedSourcesConfig = _.merge(
    {},
    configDefault.resourceConfig[ResourceType.data_provider].supportedSources,
    (configCustom.resourceConfig &&
     ResourceType.data_provider in configCustom.resourceConfig &&
     configCustom.resourceConfig[ResourceType.data_provider]?.supportedSources ?
        configCustom.resourceConfig[ResourceType.data_provider].supportedSources :
        {}
    ),
    (configHost.resourceConfig &&
     ResourceType.data_provider in configHost.resourceConfig &&
     configHost.resourceConfig[ResourceType.data_provider]?.supportedSources ?
        configHost.resourceConfig[ResourceType.data_provider].supportedSources :
        {}
    )
);

// Merge File Supported Sources
const mergedFileSupportedSourcesConfig = _.merge(
    {},
    configDefault.resourceConfig[ResourceType.file].supportedSources,
    (configCustom.resourceConfig &&
     ResourceType.file in configCustom.resourceConfig &&
     configCustom.resourceConfig[ResourceType.file]?.supportedSources ?
        configCustom.resourceConfig[ResourceType.file].supportedSources :
        {}
    ),
    (configHost.resourceConfig &&
     ResourceType.file in configHost.resourceConfig &&
     configHost.resourceConfig[ResourceType.file]?.supportedSources ?
        configHost.resourceConfig[ResourceType.file].supportedSources :
        {}
    )
);


// Perform complete overrides for other properties
const appConfig: AppConfig = {
    ...configDefault,
    ...configCustom,
    ...configHost,
    badges: mergedBadges, // Use the merged result
};

// Apply the merged supported sources
if (appConfig.resourceConfig && ResourceType.table in appConfig.resourceConfig && appConfig.resourceConfig[ResourceType.table]?.supportedSources) {
    appConfig.resourceConfig[ResourceType.table].supportedSources = mergedTableSupportedSourcesConfig
}
if (appConfig.resourceConfig && ResourceType.dashboard in appConfig.resourceConfig && appConfig.resourceConfig[ResourceType.dashboard]?.supportedSources) {
    appConfig.resourceConfig[ResourceType.dashboard].supportedSources = mergedDashboardSupportedSourcesConfig
}
if (appConfig.resourceConfig && ResourceType.data_provider in appConfig.resourceConfig && appConfig.resourceConfig[ResourceType.data_provider]?.supportedSources) {
    appConfig.resourceConfig[ResourceType.data_provider].supportedSources = mergedDataProviderSupportedSourcesConfig
}
if (appConfig.resourceConfig && ResourceType.file in appConfig.resourceConfig && appConfig.resourceConfig[ResourceType.file]?.supportedSources) {
    appConfig.resourceConfig[ResourceType.file].supportedSources = mergedFileSupportedSourcesConfig
}

export default appConfig;