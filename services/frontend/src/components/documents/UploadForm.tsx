import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadDocument } from '../../hooks/useDocuments';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input, TextArea } from '../common/Input';

export const UploadForm: React.FC = () => {
  const navigate = useNavigate();
  const uploadDocument = useUploadDocument();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    file: null as File | null,
  });

  const [errors, setErrors] = useState({
    title: '',
    file: '',
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setFormData({ ...formData, file });
    if (file) {
      setErrors({ ...errors, file: '' });
    }
  };

  const validateForm = () => {
    const newErrors = { title: '', file: '' };
    let isValid = true;

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
      isValid = false;
    }

    if (!formData.file) {
      newErrors.file = 'Please select a file to upload';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const result = await uploadDocument.mutateAsync({
        file: formData.file!,
        title: formData.title,
        description: formData.description || undefined,
      });

      // Navigate to the document detail page
      navigate(`/documents/${result.id}`);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <Card>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Document</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Title"
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          error={errors.title}
          placeholder="Enter document title"
          required
        />

        <TextArea
          label="Description (optional)"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Enter document description"
          rows={3}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            File
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-primary-500 transition-colors">
            <div className="space-y-1 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="flex text-sm text-gray-600">
                <label
                  htmlFor="file-upload"
                  className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none"
                >
                  <span>Upload a file</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    onChange={handleFileChange}
                    accept=".pdf,.docx,.txt"
                  />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">PDF, DOCX, TXT up to 100MB</p>
              {formData.file && (
                <p className="text-sm text-gray-900 font-medium">{formData.file.name}</p>
              )}
            </div>
          </div>
          {errors.file && <p className="mt-1 text-sm text-red-600">{errors.file}</p>}
        </div>

        {uploadDocument.error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">
              Upload failed: {uploadDocument.error.message}
            </p>
          </div>
        )}

        {uploadDocument.isSuccess && (
          <div className="rounded-md bg-green-50 p-4">
            <p className="text-sm text-green-800">
              Document uploaded successfully! Redirecting...
            </p>
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setFormData({ title: '', description: '', file: null })}
            disabled={uploadDocument.isPending}
          >
            Clear
          </Button>
          <Button type="submit" isLoading={uploadDocument.isPending}>
            Upload
          </Button>
        </div>
      </form>
    </Card>
  );
};
