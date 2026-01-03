# HireEdgeAI Frontend

React/Next.js frontend for the HireEdgeAI Resume Builder application.

## Features

- ✅ **Landing Page** - Professional homepage with features and CTA
- ✅ **Resume Builder** - Interactive resume builder with:
  - PDF preview (left side)
  - AI editor with chat interface (right side)
  - Resume scoring modal
  - Job description input
  - Section-based editing
- ✅ **Responsive Design** - Mobile-friendly layouts
- ✅ **Modern UI** - Clean, professional design with Tailwind CSS

## Getting Started

### Prerequisites

- Node.js 18.17+ or 20.x
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your API URL:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with toast provider
│   ├── page.tsx                # Landing page
│   ├── resume-builder/
│   │   └── page.tsx            # Resume builder page
│   └── globals.css             # Global styles
├── components/
│   ├── ui/
│   │   └── Modal.tsx           # Reusable modal component
│   └── resume/
│       └── ResumeScoringModal.tsx  # Resume scoring modal
├── lib/
│   └── api/
│       ├── client.ts           # Axios client configuration
│       └── resume-builder.ts   # Resume builder API functions
└── types/
    └── index.ts                # TypeScript types
```

## Pages

### Landing Page (`/`)
- Hero section
- Features grid
- Call-to-action sections
- Navigation header

### Resume Builder (`/resume-builder`)
- Two-column layout:
  - **Left**: PDF preview (scrollable)
  - **Right**: AI editor with:
    - Chat history
    - Job description input
    - Section buttons
    - Query input
- Header with navigation and actions
- Resume scoring modal (opens on "Check Scores" button)

## API Integration

The frontend expects a FastAPI backend running on `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`).

Key API endpoints used:
- `/api/resume/session/create` - Create new session
- `/api/resume/session/{id}/compile` - Compile LaTeX to PDF
- `/api/resume/session/{id}/pdf` - Get PDF blob
- `/api/resume/session/{id}/score` - Calculate resume scores
- `/api/resume/session/{id}/sections` - Get sections
- `/api/resume/session/{id}/chat` - Send chat message
- And more...

## Technologies

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Hook Form** - Form management
- **Zod** - Validation
- **Zustand** - State management
- **React Hot Toast** - Notifications
- **Lucide React** - Icons

## Next Steps

- [ ] Integrate real API endpoints
- [ ] Implement chat functionality
- [ ] Add file upload
- [ ] Implement section editing
- [ ] Add undo/redo functionality
- [ ] Mobile responsive improvements
- [ ] Add loading states
- [ ] Error handling improvements
