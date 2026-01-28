import React, { useState } from 'react';
import { UploadCloudIcon, XIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { uploadSingleFile } from '../../utils/github'; // Import uploadSingleFile



export const ImageUploader = ({
  onUploadSuccess,
  currentImageUrl,
  label = 'Upload Image',
}) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(currentImageUrl);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setSelectedFile(null);
      setPreviewUrl(currentImageUrl);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first.');
      return;
    }

    setUploading(true);
    try {
      // Use uploadSingleFile from github.jsx
      // Assuming a default category like 'avatars' for user avatars
      const { cdnUrl } = await uploadSingleFile(selectedFile, 'avatars'); 
      
      onUploadSuccess(cdnUrl);
      setPreviewUrl(cdnUrl);
      setSelectedFile(null);
      toast.success('Image uploaded successfully!');
    } catch (error) {
      toast.error('Failed to upload image.');
      console.error('Image upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveImage = () => {
    setSelectedFile(null);
    setPreviewUrl(undefined);
    onUploadSuccess(''); // Clear the URL in the parent form
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-border-light rounded-md">
      {previewUrl ? (
        <div className="relative w-32 h-32 mb-3">
          <img src={previewUrl} alt="Preview" className="w-full h-full object-cover rounded-md" />
          <button
            type="button"
            onClick={handleRemoveImage}
            className="absolute -top-2 -right-2 bg-error text-white rounded-full p-1 shadow-md"
          >
            <XIcon size={16} />
          </button>
        </div>
      ) : (
        <div className="text-copy-light mb-3 text-center">
          <UploadCloudIcon size={32} className="mx-auto mb-2" />
          <p className="text-sm">{label}</p>
        </div>
      )}

      <input
        type="file"
        id="image-upload"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
      <label
        htmlFor="image-upload"
        className="cursor-pointer px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors text-sm"
      >
        {selectedFile ? 'Change Image' : 'Select Image'}
      </label>
      {selectedFile && (
        <button
          type="button"
          onClick={handleUpload}
          disabled={uploading}
          className="mt-2 px-4 py-2 bg-secondary text-white rounded-md hover:bg-secondary-dark transition-colors text-sm disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      )}
    </div>
  );
};
