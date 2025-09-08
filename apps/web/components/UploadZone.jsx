'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Alert,
  Button,
} from '@mui/material';
import { CloudUpload, CheckCircle, Error } from '@mui/icons-material';
import { uploadDocs } from '../lib/api';

const UploadZone = ({ botId, onUploadComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!botId) {
      setError('Please select a bot first');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    setUploadStatus('PENDING');

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await uploadDocs(botId, acceptedFiles);
      
      clearInterval(progressInterval);
      setProgress(100);
      setUploadStatus('DONE');
      
      setTimeout(() => {
        setUploading(false);
        setProgress(0);
        setUploadStatus(null);
        if (onUploadComplete) {
          onUploadComplete(result);
        }
      }, 1000);

    } catch (err) {
      setError(err.message);
      setUploadStatus('ERROR');
      setUploading(false);
      setProgress(0);
    }
  }, [botId, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: 30 * 1024 * 1024, // 30MB limit
  });

  const getStatusColor = () => {
    switch (uploadStatus) {
      case 'DONE':
        return 'success';
      case 'ERROR':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'DONE':
        return <CheckCircle />;
      case 'ERROR':
        return <Error />;
      default:
        return null;
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Upload Documents
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            or click to select files
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Supports: PDF, DOCX, TXT, CSV, XLSX (max 30MB each)
          </Typography>
        </Box>

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Uploading...</Typography>
              <Typography variant="body2">{progress}%</Typography>
            </Box>
            <LinearProgress variant="determinate" value={progress} />
            {uploadStatus && (
              <Chip
                icon={getStatusIcon()}
                label={uploadStatus}
                color={getStatusColor()}
                size="small"
                sx={{ mt: 1 }}
              />
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default UploadZone;
