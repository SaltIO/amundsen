

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