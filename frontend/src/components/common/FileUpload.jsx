import { useState, useRef } from 'react';
import { useFileUpload, formatFileSize, isImageFile, createFilePreview, cleanupFilePreview } from '../../hooks/useFileUpload';
import { FiUpload, FiX, FiFile, FiTrash2, FiCheck } from 'react-icons/fi';
import { toast } from 'react-hot-toast';

const FileUpload = ({
  category = 'uploads',
  maxSizeKB = 100,
  allowedTypes,
  multiple = false,
  accept,
  onUploadSuccess,
  onUploadError,
  className = '',
  disabled = false,
  showPreview = true,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [filePreviews, setFilePreviews] = useState([]);
  const fileInputRef = useRef(null);

  const {
    loading,
    progress,
    error,
    uploadedFiles,
    uploadFiles,
    deleteFiles,
    validateFiles,
    reset,
  } = useFileUpload({
    category,
    maxSizeKB,
    allowedTypes,
    onSuccess: (files) => {
      onUploadSuccess?.(files);
      filePreviews.forEach(preview => {
        if (preview.preview) {
          cleanupFilePreview(preview.preview);
        }
      });
      setFilePreviews([]);
    },
    onError: (error) => {
      onUploadError?.(error.message);
    },
  });

  const handleFiles = (files) => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    
    const { valid, errors } = validateFiles(fileArray);
    
    if (errors.length > 0) {
      toast.error(`File validation failed:\n${errors.join('\n')}`);
      return;
    }

    const previews = valid.map(file => ({
      file,
      preview: isImageFile(file) ? createFilePreview(file) : undefined,
      id: Math.random().toString(36).substring(7),
    }));

    setFilePreviews(previews);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (disabled) return;
    
    const files = e.dataTransfer.files;
    handleFiles(files);
  };

  const handleInputChange = (e) => {
    handleFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (filePreviews.length === 0) return;
    
    const files = filePreviews.map(preview => preview.file);
    await uploadFiles(files);
  };

  const removePreview = (id) => {
    setFilePreviews(prev => {
      const updated = prev.filter(preview => {
        if (preview.id === id) {
          if (preview.preview) {
            cleanupFilePreview(preview.preview);
          }
          return false;
        }
        return true;
      });
      return updated;
    });
  };

  const handleDeleteUploaded = async (githubPath) => {
    await deleteFiles([{ githubPath }]);
  };

  const openFileDialog = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const clearAll = () => {
    filePreviews.forEach(preview => {
      if (preview.preview) {
        cleanupFilePreview(preview.preview);
      }
    });
    setFilePreviews([]);
    reset();
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`file-upload ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled}
      />

      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center transition-colors
          ${dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <FiUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {dragActive ? 'Drop files here' : 'Upload files'}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
          Drag and drop files here, or click to select
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500">
          Max size: {maxSizeKB}KB • {multiple ? 'Multiple files allowed' : 'Single file only'}
        </p>
        
        {loading && (
          <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center rounded-lg">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Uploading... {progress}%
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error.message}</p>
        </div>
      )}

      {showPreview && filePreviews.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white">
              Files to upload ({filePreviews.length})
            </h4>
            <div className="flex gap-2">
              <button
                onClick={handleUpload}
                disabled={loading || filePreviews.length === 0}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <FiUpload className="w-3 h-3" />
                Upload
              </button>
              <button
                onClick={clearAll}
                disabled={loading}
                className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <FiX className="w-3 h-3" />
                Clear
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filePreviews.map((preview) => (
              <div key={preview.id} className="relative border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <div className="flex items-start gap-3">
                  {preview.preview ? (
                    <img
                      src={preview.preview}
                      alt={preview.file.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
                      <FiFile className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {preview.file.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(preview.file.size)}
                    </p>
                  </div>
                  
                  <button
                    onClick={() => removePreview(preview.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <FiX className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <FiCheck className="w-4 h-4 text-green-500" />
            Uploaded files ({uploadedFiles.length})
          </h4>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="relative border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                <div className="flex items-start gap-3">
                  {isImageFile({ type: file.type }) ? (
                    <img
                      src={file.url}
                      alt={file.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
                      <FiFile className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(file.size)}
                    </p>
                    <a
                      href={file.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View file
                    </a>
                  </div>
                  
                  <button
                    onClick={() => handleDeleteUploaded(file.githubPath)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                    disabled={loading}
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;