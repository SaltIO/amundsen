import * as React from 'react';
import axios from 'axios';

import './styles.scss';

export const API_PATH = '/api/file_upload/v0';

interface FileUploadState {
  selectedFile: File | null;
  uploadProgress: number;
  uploadId: string | null;
}

interface UploadedPart {
  PartNumber: number;
  ETag: string;
}

export class FileUploadComponent extends React.Component<{}, FileUploadState> {
  constructor(props: {}) {
    super(props);
    this.state = {
      selectedFile: null,
      uploadProgress: 0,
      uploadId: null,
    };

    this.handleFileChange = this.handleFileChange.bind(this);
    this.uploadFileInChunks = this.uploadFileInChunks.bind(this);
    this.completeMultipartUpload = this.completeMultipartUpload.bind(this);
  }

  // Handle file selection
  handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    if (event.target.files && event.target.files.length > 0) {
      this.setState({
        selectedFile: event.target.files[0],
      });
    }
  }

  // Initiate multipart upload
  async initiateMultipartUpload(fileName: string, fileType: string) {
    try {
      const response = await axios.post(`${API_PATH}/initiate_multipart_upload`, {
        fileName,
        fileType,
      });

      this.setState({ uploadId: response.data.uploadId });
    } catch (error) {
      console.error('Error initiating multipart upload:', error);
    }
  }

  // Upload each chunk with presigned URL
  async uploadFileInChunks() {
    const { selectedFile, uploadId } = this.state;

    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    if (!uploadId) {
      await this.initiateMultipartUpload(selectedFile.name, selectedFile.type);

      // After initiating, wait for the state to be updated with the uploadId
      const { uploadId: newUploadId } = this.state;
      if (!newUploadId) {
        console.error('Failed to initiate multipart upload.');
        return;
      }
    }

    const chunkSize = 5 * 1024 * 1024; // 5 MB per chunk
    const totalChunks = Math.ceil(selectedFile.size / chunkSize);
    let uploadedParts: UploadedPart[] = [];

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      const start = chunkIndex * chunkSize;
      const end = Math.min(start + chunkSize, selectedFile.size);
      const fileChunk = selectedFile.slice(start, end);

      // Get presigned URL for the specific chunk
      const { uploadId: activeUploadId } = this.state;
      const response = await axios.post(`${API_PATH}/get_presigned_url`, {
        fileName: selectedFile.name,
        uploadId: activeUploadId,
        partNumber: chunkIndex + 1,
        contentType: selectedFile.type,
      });

      const presignedUrl = response.data.url;

      // Upload the chunk
      const uploadResponse = await axios.put(presignedUrl, fileChunk, {
        headers: {
          'Content-Type': selectedFile.type,
        },
      });

      uploadedParts.push({
        PartNumber: chunkIndex + 1,
        ETag: uploadResponse.headers.etag,
      });

      // Update upload progress
      this.setState({
        uploadProgress: Math.floor(((chunkIndex + 1) / totalChunks) * 100),
      });
    }

    // Complete the multipart upload
    await this.completeMultipartUpload(uploadedParts);
  }

  // Complete multipart upload
  async completeMultipartUpload(parts: any) {
    const { selectedFile, uploadId } = this.state;

    try {
      await axios.post(`${API_PATH}/complete_multipart_upload`, {
        fileName: selectedFile!.name,
        uploadId: uploadId!,
        parts: parts,
      });
      alert('File uploaded successfully!');
    } catch (error) {
      console.error('Error completing multipart upload:', error);
    } finally {
      this.setState({
        uploadId: null,
      });
    }
  }

  render() {
    const { selectedFile, uploadProgress } = this.state;

    return (
      <div className="file-upload-container">
        <h1 className="file-upload-title">CMD+RVL Metadata File Upload</h1>
        <input className="file-upload-input" type="file" onChange={this.handleFileChange} />
        {selectedFile && (
          <div>
            <div className="file-upload-selected-file">
              <p>Selected File: {selectedFile.name}</p>
            </div>
            <div>
              <button className="btn btn-primary file-upload-button" onClick={this.uploadFileInChunks}>Upload</button>
            </div>
          </div>
        )}

        {uploadProgress > 0 && (
          <div className="file-upload-progress-bar">
            <div className="file-upload-progress-bar-inner" style={{ width: `${uploadProgress}%` }}></div>
          </div>
        )}
      </div>
    );
  }
}

export default FileUploadComponent;