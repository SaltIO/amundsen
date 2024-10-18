import React, { useState } from 'react';
// import * as React from 'react';

// import { logClick } from 'utils/analytics';

import './styles.scss';

interface FileUploadProps {}

const FileUpload: React.FC<FileUploadProps> = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [partSize] = useState(5 * 1024 * 1024); // 5MB part size
  const [parts, setParts] = useState<Array<{ ETag: string; PartNumber: number }>>([]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const startMultipartUpload = async () => {
    const response = await fetch('/start-multipart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile?.name,
        contentType: selectedFile?.type,
      }),
    });
    const { uploadId } = await response.json();
    setUploadId(uploadId);
  };

  const uploadPart = async (fileChunk: Blob, partNumber: number) => {
    const response = await fetch('/presigned-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uploadId,
        key: selectedFile?.name,
        partNumber,
      }),
    });

    const { presignedUrl } = await response.json();

    const uploadResponse = await fetch(presignedUrl, {
      method: 'PUT',
      headers: { 'Content-Type': selectedFile?.type || 'application/octet-stream' },
      body: fileChunk,
    });

    const part = {
      ETag: uploadResponse.headers.get('ETag') as string,
      PartNumber: partNumber,
    };

    setParts((prevParts) => [...prevParts, part]);
  };

  const completeMultipartUpload = async () => {
    const response = await fetch('/complete-multipart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uploadId,
        key: selectedFile?.name,
        parts,
      }),
    });

    await response.json();
    alert('File uploaded successfully!');
  };

  const uploadFileInParts = async () => {
    if (!selectedFile) return;

    await startMultipartUpload();

    const totalParts = Math.ceil(selectedFile.size / partSize);

    // Explicitly define the type of the array as Promise<void>[]
    const uploadPromises: Promise<void>[] = [];

    for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
      const start = (partNumber - 1) * partSize;
      const end = Math.min(start + partSize, selectedFile.size);
      const fileChunk = selectedFile.slice(start, end);

      // Push the promises returned from uploadPart into the array
      uploadPromises.push(uploadPart(fileChunk, partNumber));
    }

    // Wait for all parts to finish uploading
    await Promise.all(uploadPromises);

    // Complete the multipart upload
    await completeMultipartUpload();
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={uploadFileInParts}>Upload File</button>
    </div>
  );
};

export default FileUpload;