'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Send, SmartToy } from '@mui/icons-material';
import { streamChatResponse } from '../lib/sse';
import SourcesPopover from './SourcesPopover';

const ChatBox = ({ botSlug, botName }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [sourcesAnchorEl, setSourcesAnchorEl] = useState(null);
  const [currentSources, setCurrentSources] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Add user message
    const newUserMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newUserMessage]);

    // Add assistant message placeholder
    const assistantMessageId = Date.now() + 1;
    const newAssistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      sources: [],
    };

    setMessages(prev => [...prev, newAssistantMessage]);
    setIsStreaming(true);

    try {
      let accumulatedContent = '';
      let sources = [];

      for await (const chunk of streamChatResponse(botSlug, userMessage)) {
        if (chunk.type === 'text' || chunk.content) {
          const content = chunk.content || chunk.text || '';
          accumulatedContent += content;
          
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: accumulatedContent }
                : msg
            )
          );
        } else if (chunk.sources) {
          sources = chunk.sources;
          setCurrentSources(sources);
          
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, sources }
                : msg
            )
          );
        }
      }
    } catch (err) {
      setError(err.message);
      // Remove the assistant message if there was an error
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCitationClick = (event, sources) => {
    setCurrentSources(sources);
    setSourcesAnchorEl(event.currentTarget);
  };

  const handleSourcesClose = () => {
    setSourcesAnchorEl(null);
  };

  // Function to render text with citations
  const renderTextWithCitations = (text, sources) => {
    if (!text || !sources || sources.length === 0) {
      return text;
    }

    // Simple regex to find citation patterns like [1], [2], etc.
    const parts = text.split(/(\[\d+\])/g);
    
    return parts.map((part, index) => {
      const citationMatch = part.match(/\[(\d+)\]/);
      if (citationMatch) {
        const citationIndex = parseInt(citationMatch[1]) - 1;
        const source = sources[citationIndex];
        
        if (source) {
          return (
            <span
              key={index}
              style={{
                color: '#1976d2',
                cursor: 'pointer',
                textDecoration: 'underline',
                fontWeight: 'bold',
              }}
              onClick={(e) => handleCitationClick(e, [source])}
            >
              {part}
            </span>
          );
        }
      }
      return part;
    });
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper 
        sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Messages Area */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}>
          {messages.length === 0 && (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary',
            }}>
              <SmartToy sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                Start a conversation with {botName || 'your bot'}
              </Typography>
              <Typography variant="body2">
                Ask questions about your uploaded documents
              </Typography>
            </Box>
          )}

          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  backgroundColor: message.role === 'user' ? 'primary.main' : 'grey.100',
                  color: message.role === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {renderTextWithCitations(message.content, message.sources)}
                </Typography>
                
                {message.sources && message.sources.length > 0 && (
                  <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary">
                      Sources: {message.sources.map((_, i) => `[${i + 1}]`).join(' ')}
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Box>
          ))}

          {isStreaming && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    Thinking...
                  </Typography>
                </Box>
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              disabled={isStreaming}
              variant="outlined"
              size="small"
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
              sx={{ minWidth: 'auto', px: 2 }}
            >
              <Send />
            </Button>
          </Box>
        </Box>
      </Paper>

      <SourcesPopover
        anchorEl={sourcesAnchorEl}
        open={Boolean(sourcesAnchorEl)}
        onClose={handleSourcesClose}
        sources={currentSources}
      />
    </Box>
  );
};

export default ChatBox;
