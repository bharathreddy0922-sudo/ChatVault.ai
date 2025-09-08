# Source-Grounded Research Copilot - Frontend

A Next.js frontend for the Source-Grounded Research Copilot, optimized for M1 MacBooks with 8GB RAM.

## Features

- **Modern UI**: Clean Material-UI interface with responsive design
- **Real-time Chat**: Streaming responses with source citations
- **File Upload**: Drag & drop with progress tracking
- **Bot Management**: Create, manage, and chat with research bots
- **Source Citations**: Inline footnotes with hover previews
- **M1 Optimized**: Lightweight dependencies and efficient rendering

## Quick Start

### Prerequisites

- Node.js 18+ 
- Backend API running on http://localhost:8000

### Installation

```bash
cd apps/web
npm install
```

### Environment Setup

Create a `.env.local` file in the `apps/web` directory:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000 to access the application.

## Project Structure

```
apps/web/
├── app/                    # Next.js App Router
│   ├── layout.js          # Root layout with providers
│   ├── page.js            # Dashboard page
│   └── chat/[slug]/       # Dynamic chat pages
├── components/            # React components
│   ├── UploadZone.jsx     # File upload with drag & drop
│   ├── ChatBox.jsx        # Chat interface with streaming
│   ├── SourcesPopover.jsx # Citation source previews
│   ├── BotHeader.jsx      # Bot info and actions
│   └── LibraryTable.jsx   # Document library table
├── lib/                   # Utilities and API
│   ├── client.js          # React Query configuration
│   ├── api.js             # API wrapper functions
│   └── sse.js             # Server-Sent Events helper
├── theme.js               # MUI theme configuration
└── package.json           # Dependencies
```

## Key Components

### UploadZone
- Drag & drop file upload
- Progress tracking
- File type validation (PDF, DOCX, TXT, CSV, XLSX)
- 30MB file size limit

### ChatBox
- Real-time streaming chat
- Inline citations [1][2]
- Source hover previews
- Error handling

### SourcesPopover
- Displays source information
- Document name and location
- Text excerpts
- Clickable citations

## API Integration

The frontend communicates with the FastAPI backend through:

- **Bot Management**: Create, list, and manage research bots
- **Document Upload**: Multi-file upload with progress tracking
- **Chat Streaming**: Server-Sent Events for real-time responses
- **Library Management**: View uploaded documents and their status

## M1 Optimizations

- **Lightweight Dependencies**: Minimal package footprint
- **Efficient Rendering**: Optimized React components
- **Streaming**: Real-time updates without heavy polling
- **Memory Management**: Proper cleanup and resource management

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Backend Requirements

Ensure the FastAPI backend is running with:

```bash
cd apps/api
uv run uvicorn src.main:app --reload --port 8000
```

## Vertical Slice Testing

1. **Create Bot**: Visit dashboard and create a new research bot
2. **Upload Documents**: Drag & drop PDF/DOCX files
3. **Chat**: Click "Go to Chat" and ask questions
4. **Citations**: Hover over [1][2] citations to see sources
5. **Multi-doc**: Ask questions spanning multiple documents

## Troubleshooting

### Common Issues

1. **Backend Connection**: Ensure FastAPI is running on port 8000
2. **File Upload**: Check file size limits (30MB) and supported formats
3. **Streaming**: Verify SSE endpoints are working correctly
4. **Citations**: Ensure backend returns proper source metadata

### Getting Help

- Check browser console for errors
- Verify backend API endpoints are responding
- Review network tab for failed requests
- Check environment variables are set correctly

## License

This project is licensed under the MIT License.
