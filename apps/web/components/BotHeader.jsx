'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import { Add, Language } from '@mui/icons-material';
import { addUrls } from '../lib/api';

const BotHeader = ({ bot, onRefresh }) => {
  const [urlDialogOpen, setUrlDialogOpen] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [depth, setDepth] = useState(1);
  const [renderJs, setRenderJs] = useState(false);
  const [addingUrl, setAddingUrl] = useState(false);
  const [urlError, setUrlError] = useState(null);

  const handleAddUrl = async () => {
    if (!urlInput.trim()) return;

    setAddingUrl(true);
    setUrlError(null);

    try {
      await addUrls(bot.id, urlInput.trim(), depth, renderJs);
      setUrlDialogOpen(false);
      setUrlInput('');
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      setUrlError(error.message);
    } finally {
      setAddingUrl(false);
    }
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {bot?.name || 'Research Bot'}
          </Typography>
          {bot?.description && (
            <Typography variant="body1" color="text.secondary">
              {bot.description}
            </Typography>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Language />}
            onClick={() => setUrlDialogOpen(true)}
          >
            Add URL
          </Button>
        </Box>
      </Box>

      {/* URL Dialog */}
      <Dialog open={urlDialogOpen} onClose={() => setUrlDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add URL for Crawling</DialogTitle>
        <DialogContent>
          {urlError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {urlError}
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="URL"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://example.com"
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Crawl Depth"
            type="number"
            value={depth}
            onChange={(e) => setDepth(parseInt(e.target.value) || 1)}
            inputProps={{ min: 1, max: 3 }}
            helperText="How deep to crawl (1-3 levels)"
            sx={{ mb: 2 }}
          />
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <input
              type="checkbox"
              id="renderJs"
              checked={renderJs}
              onChange={(e) => setRenderJs(e.target.checked)}
            />
            <label htmlFor="renderJs">
              <Typography variant="body2">
                Render JavaScript (requires Playwright)
              </Typography>
            </label>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUrlDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleAddUrl} 
            variant="contained"
            disabled={!urlInput.trim() || addingUrl}
          >
            {addingUrl ? 'Adding...' : 'Add URL'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BotHeader;
