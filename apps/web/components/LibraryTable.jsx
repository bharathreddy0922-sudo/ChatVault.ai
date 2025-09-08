'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Box,
} from '@mui/material';
import { Description, CheckCircle, Error, HourglassEmpty } from '@mui/icons-material';

const LibraryTable = ({ documents = [] }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'DONE':
        return <CheckCircle color="success" />;
      case 'ERROR':
        return <Error color="error" />;
      case 'PENDING':
      case 'PARSING':
      case 'CHUNKING':
      case 'EMBEDDING':
        return <HourglassEmpty color="warning" />;
      default:
        return <Description />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'DONE':
        return 'success';
      case 'ERROR':
        return 'error';
      case 'PENDING':
      case 'PARSING':
      case 'CHUNKING':
      case 'EMBEDDING':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (documents.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Description sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          No documents uploaded yet
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload some documents to get started
        </Typography>
      </Paper>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Document</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Size</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Pages</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getStatusIcon(doc.status)}
                  <Typography variant="body2">
                    {doc.filename}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip 
                  label={doc.filetype?.toUpperCase() || 'Unknown'} 
                  size="small" 
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {formatFileSize(doc.size)}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={doc.status}
                  color={getStatusColor(doc.status)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {doc.pages || 'N/A'}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default LibraryTable;
