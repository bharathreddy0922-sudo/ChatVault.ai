'use client';

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getBots } from '../../../lib/api';
import ChatBox from '../../../components/ChatBox';
import UploadZone from '../../../components/UploadZone';
import BotHeader from '../../../components/BotHeader';

export default function ChatPage({ params }) {
  const { slug } = params;
  const [bot, setBot] = useState(null);

  // Fetch bots to find the one with matching slug
  const { data: bots = [], isLoading, error } = useQuery({
    queryKey: ['bots'],
    queryFn: getBots,
  });

  useEffect(() => {
    if (bots.length > 0) {
      const foundBot = bots.find(b => b.slug === slug);
      setBot(foundBot);
    }
  }, [bots, slug]);

  const handleRefresh = () => {
    // This would typically refetch the library data
    window.location.reload();
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Error loading bot: {error.message}
        </Alert>
      </Container>
    );
  }

  if (!bot) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">
          Bot not found. Please check the URL or create a new bot.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <BotHeader bot={bot} onRefresh={handleRefresh} />
      
      <Grid container spacing={3}>
        {/* Chat Area */}
        <Grid item xs={12} md={8}>
          <Box sx={{ height: '70vh' }}>
            <ChatBox botSlug={slug} botName={bot.name} />
          </Box>
        </Grid>
        
        {/* Upload Area */}
        <Grid item xs={12} md={4}>
          <UploadZone 
            botId={bot.id} 
            onUploadComplete={handleRefresh}
          />
        </Grid>
      </Grid>
    </Container>
  );
}
