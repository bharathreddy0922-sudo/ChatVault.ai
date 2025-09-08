'use client';

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Add, SmartToy, Description } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createBot, getBots, getLibrary } from '../lib/api';
import UploadZone from '../components/UploadZone';
import LibraryTable from '../components/LibraryTable';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const [botName, setBotName] = useState('');
  const [botDescription, setBotDescription] = useState('');
  const [selectedBot, setSelectedBot] = useState(null);
  const router = useRouter();

  // Queries
  const { data: bots = [], refetch: refetchBots } = useQuery({
    queryKey: ['bots'],
    queryFn: getBots,
  });

  const { data: library = [], refetch: refetchLibrary } = useQuery({
    queryKey: ['library'],
    queryFn: getLibrary,
  });

  // Mutations
  const createBotMutation = useMutation({
    mutationFn: ({ name, description }) => createBot(name, description),
    onSuccess: (data) => {
      setBotName('');
      setBotDescription('');
      refetchBots();
      setSelectedBot(data);
    },
  });

  const handleCreateBot = () => {
    if (!botName.trim()) return;
    
    createBotMutation.mutate({
      name: botName.trim(),
      description: botDescription.trim(),
    });
  };

  const handleUploadComplete = () => {
    refetchLibrary();
  };

  const handleGoToChat = (bot) => {
    router.push(`/chat/${bot.slug}`);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom align="center">
        Source-Grounded Research Copilot
      </Typography>
      <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
        Upload documents and chat with them using AI-powered research assistance
      </Typography>

      <Grid container spacing={4}>
        {/* Create Bot Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Add sx={{ mr: 1 }} />
                <Typography variant="h5">Create New Bot</Typography>
              </Box>
              
              <TextField
                fullWidth
                label="Bot Name"
                value={botName}
                onChange={(e) => setBotName(e.target.value)}
                placeholder="e.g., Demo Research Bot"
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Description (optional)"
                value={botDescription}
                onChange={(e) => setBotDescription(e.target.value)}
                placeholder="What will this bot help you research?"
                multiline
                rows={2}
                sx={{ mb: 2 }}
              />
              
              <Button
                fullWidth
                variant="contained"
                onClick={handleCreateBot}
                disabled={!botName.trim() || createBotMutation.isPending}
                startIcon={createBotMutation.isPending ? <CircularProgress size={16} /> : <Add />}
              >
                {createBotMutation.isPending ? 'Creating...' : 'Create Bot'}
              </Button>

              {createBotMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {createBotMutation.error.message}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Recent Bots */}
          {bots.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Bots
                </Typography>
                {bots.slice(0, 3).map((bot) => (
                  <Box
                    key={bot.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      p: 1,
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <Box>
                      <Typography variant="subtitle1">{bot.name}</Typography>
                      {bot.description && (
                        <Typography variant="body2" color="text.secondary">
                          {bot.description}
                        </Typography>
                      )}
                    </Box>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleGoToChat(bot)}
                    >
                      Chat
                    </Button>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Description sx={{ mr: 1 }} />
                <Typography variant="h5">Upload Documents</Typography>
              </Box>
              
              {selectedBot ? (
                <>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Bot "{selectedBot.name}" created successfully! You can now upload documents.
                  </Alert>
                  <UploadZone 
                    botId={selectedBot.id} 
                    onUploadComplete={handleUploadComplete}
                  />
                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={() => handleGoToChat(selectedBot)}
                      startIcon={<SmartToy />}
                    >
                      Go to Chat
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setSelectedBot(null)}
                    >
                      Create Another Bot
                    </Button>
                  </Box>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Description sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Create a bot first
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Create a research bot to start uploading documents
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Library Section */}
      {library.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Document Library
          </Typography>
          <LibraryTable documents={library} />
        </Box>
      )}
    </Container>
  );
}
