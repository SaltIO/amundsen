

export interface DataLocation {
    key: string
    name: string
    type: string
}

export interface FilesystemDataLocation extends DataLocation {
    drive: string
}

export interface AwsS3DataLocation extends DataLocation {
    bucket: string
}

export function isFilesystemDataLocation(dataLocation: any): dataLocation is FilesystemDataLocation {
    return dataLocation !== null &&
           typeof dataLocation === 'object' &&
           'drive' in dataLocation;
}

export function isAwsS3DataLocation(dataLocation: any): dataLocation is AwsS3DataLocation {
    return dataLocation !== null &&
           typeof dataLocation === 'object' &&
           'bucket' in dataLocation;
}