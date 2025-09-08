'use client';

import React from 'react';
import {
  Popover,
  Typography,
  Box,
  Chip,
  Divider,
} from '@mui/material';
import { Description, Pageview } from '@mui/icons-material';

const SourcesPopover = ({ anchorEl, open, onClose, sources = [] }) => {
  const handleClose = () => {
    onClose();
  };

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={handleClose}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'left',
      }}
      transformOrigin={{
        vertical: 'bottom',
        horizontal: 'left',
      }}
      PaperProps={{
        sx: {
          maxWidth: 400,
          maxHeight: 300,
          overflow: 'auto',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Sources
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        {sources.map((source, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Description sx={{ fontSize: 16, mr: 1, color: 'primary.main' }} />
              <Typography variant="subtitle2" sx={{ flex: 1 }}>
                {source.document_name || source.filename || 'Unknown Document'}
              </Typography>
            </Box>
            
            {source.location && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Pageview sx={{ fontSize: 14, mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  {source.location.page && `Page ${source.location.page}`}
                  {source.location.paragraph && `, Paragraph ${source.location.paragraph}`}
                  {source.location.cell && `, Cell ${source.location.cell}`}
                </Typography>
              </Box>
            )}
            
            {source.text && (
              <Typography
                variant="body2"
                sx={{
                  backgroundColor: 'grey.50',
                  p: 1,
                  borderRadius: 1,
                  fontStyle: 'italic',
                  fontSize: '0.875rem',
                }}
              >
                "{source.text.length > 200 
                  ? `${source.text.substring(0, 200)}...` 
                  : source.text}"
              </Typography>
            )}
            
            {index < sources.length - 1 && <Divider sx={{ mt: 2 }} />}
          </Box>
        ))}
      </Box>
    </Popover>
  );
};

export default SourcesPopover;
