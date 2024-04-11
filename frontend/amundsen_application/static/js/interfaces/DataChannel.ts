
import { ProviderMetadata } from './ProviderMetadata';

export interface DataChannel {
    key: string
    name: string
    type: string
    url: string
    license: string
    dataProvider?: ProviderMetadata
}
