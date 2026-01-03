# React/Next.js Migration Plan

## Complete Step-by-Step Migration Guide

This document outlines the complete plan to migrate from Streamlit to a professional React/Next.js frontend while maintaining all existing functionality.

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Project Setup](#project-setup)
3. [Design System & UI/UX](#design-system--uiux)
4. [Component Structure](#component-structure)
5. [API Integration](#api-integration)
6. [Pages & Routes](#pages--routes)
7. [State Management](#state-management)
8. [Detailed Implementation Steps](#detailed-implementation-steps)
9. [Responsive Design Strategy](#responsive-design-strategy)
10. [Professional Polish](#professional-polish)

---

## 🎯 Overview & Architecture

### Current Applications Analysis

**Application 1: AI Document Assistant (app.py)**
- 4 document types: Resume, SOP, Cover Letter, Visa Cover Letter
- Form-based input → AI generation → Payment → Download
- Features: Preview (watermarked), Payment verification (Razorpay), Format selection (DOCX/PDF)

**Application 2: Resume Builder (builder_app.py)**
- Real-time LaTeX editing with PDF preview
- Resume scoring (ATS Universal, HBPS, ATS with JD)
- AI chat interface with section-based editing
- File upload (TEX, PDF, DOCX)
- Version history (Undo/Redo)
- Job description integration

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Landing    │  │  Resume      │  │ Resume       │    │
│  │   Page       │  │  Builder     │  │ Generator    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │     SOP      │  │ Cover Letter │  │ Visa Cover   │    │
│  │  Generator   │  │  Generator   │  │ Letter Gen   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ HTTP/REST
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Resume   │  │ Document │  │ Payment  │  │   File   │  │
│  │ Builder  │  │ Generator│  │ Verify   │  │ Handling │  │
│  │  API     │  │  API     │  │  API     │  │   API    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Project Setup

### Step 1: Initialize Next.js Project

```bash
# Create Next.js 14+ app with TypeScript and Tailwind
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir

cd frontend

# Install core dependencies
npm install axios react-hook-form @hookform/resolvers zod
npm install zustand  # Lightweight state management
npm install react-hot-toast  # Toast notifications
npm install lucide-react  # Icons

# Install UI library (shadcn/ui)
npx shadcn-ui@latest init
# Select: TypeScript, Tailwind, Default style, CSS variables

# Install shadcn components
npx shadcn-ui@latest add button input textarea select card
npx shadcn-ui@latest add dialog tabs form label separator
npx shadcn-ui@latest add toast progress badge alert
npx shadcn-ui@latest add skeleton spinner

# Development dependencies
npm install -D @types/node
```

### Step 2: Project Structure

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout (Nav + Footer)
│   ├── page.tsx                   # Landing page
│   ├── resume-builder/
│   │   └── page.tsx               # Resume Builder (interactive)
│   ├── resume/
│   │   └── page.tsx               # Resume Generator (form-based)
│   ├── sop/
│   │   └── page.tsx
│   ├── cover-letter/
│   │   └── page.tsx
│   ├── visa-cover-letter/
│   │   └── page.tsx
│   ├── api/                       # Next.js API routes (proxy if needed)
│   └── globals.css                # Global styles
│
├── components/
│   ├── ui/                        # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── ...
│   │
│   ├── layout/
│   │   ├── Header.tsx             # Navigation header
│   │   ├── Footer.tsx             # Footer
│   │   └── Sidebar.tsx            # Mobile sidebar
│   │
│   ├── resume-builder/
│   │   ├── PDFPreview.tsx         # PDF viewer component
│   │   ├── ResumeScoring.tsx      # Score display (ATS, HBPS, etc.)
│   │   ├── AIChatInterface.tsx    # Chat UI for AI edits
│   │   ├── SectionButtons.tsx     # Section selection buttons
│   │   ├── JobDescriptionInput.tsx
│   │   └── FileUpload.tsx
│   │
│   ├── forms/
│   │   ├── ResumeForm.tsx         # Resume generator form
│   │   ├── SopForm.tsx
│   │   ├── CoverLetterForm.tsx
│   │   └── VisaCoverLetterForm.tsx
│   │
│   ├── shared/
│   │   ├── PaymentVerification.tsx
│   │   ├── FileDownload.tsx
│   │   ├── PreviewDisplay.tsx
│   │   ├── FormatSelector.tsx
│   │   └── LoadingSpinner.tsx
│   │
│   └── landing/
│       ├── Hero.tsx
│       ├── Features.tsx
│       ├── Pricing.tsx
│       └── Testimonials.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts              # Axios instance
│   │   ├── resume-builder.ts      # Resume builder API calls
│   │   ├── document-generator.ts  # Document generation API
│   │   ├── payments.ts            # Payment verification
│   │   └── files.ts               # File upload/download
│   │
│   ├── hooks/
│   │   ├── useResumeBuilder.ts    # Resume builder state
│   │   ├── useDocumentGenerator.ts
│   │   └── useSession.ts          # Session management
│   │
│   ├── utils/
│   │   ├── validation.ts          # Zod schemas
│   │   ├── formatters.ts          # Data formatting
│   │   └── constants.ts           # App constants
│   │
│   └── store/
│       ├── resumeBuilderStore.ts  # Zustand store
│       └── sessionStore.ts
│
├── types/
│   ├── index.ts                   # Shared types
│   ├── resume.ts                  # Resume-specific types
│   ├── api.ts                     # API response types
│   └── forms.ts                   # Form types
│
├── public/
│   ├── images/
│   └── fonts/
│
├── .env.local                     # Environment variables
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

---

## 🎨 Design System & UI/UX

### Design Principles

1. **Modern & Professional**
   - Clean, minimalist design
   - Consistent spacing and typography
   - Professional color palette
   - Smooth animations and transitions

2. **Responsive First**
   - Mobile-first approach
   - Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px)
   - Touch-friendly interactions
   - Optimized for all screen sizes

3. **Accessibility**
   - WCAG 2.1 AA compliant
   - Keyboard navigation
   - Screen reader support
   - High contrast ratios

### Color Palette

```typescript
// tailwind.config.ts
colors: {
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',   // Main brand blue
    600: '#2563eb',
    700: '#1d4ed8',
  },
  secondary: {
    500: '#8b5cf6',   // Purple accent
  },
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    900: '#111827',
  }
}
```

### Typography

- **Headings**: Inter (sans-serif)
- **Body**: Inter or system font stack
- **Monospace**: Fira Code (for code/LaTeX preview)

### Visual Design Mockups

#### Landing Page

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  HireEdgeAI      [Features] [Pricing] [Sign In]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│              🚀 Professional Documents Made Easy             │
│                                                              │
│     AI-powered resume, SOP, and cover letter generator      │
│     that helps you create ATS-friendly documents            │
│                                                              │
│     [Get Started]  [View Demo]                              │
│                                                              │
│     [Hero Image/Illustration]                               │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  ✨ Features                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ 📄 Resume│  │ 🎓 SOP   │  │ ✉️ Cover │                │
│  │ Builder  │  │ Generator│  │ Letter   │                │
│  │ Live Edit│  │          │  │          │                │
│  └──────────┘  └──────────┘  └──────────┘                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ 📊 ATS   │  │ 🤖 AI    │  │ 💳 Safe  │                │
│  │ Scoring  │  │ Powered  │  │ Payment  │                │
│  └──────────┘  └──────────┘  └──────────┘                │
│                                                              │
│  💰 Pricing                                                  │
│  [Pricing Cards]                                             │
│                                                              │
│  📞 Footer                                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Resume Builder Page

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] HireEdgeAI                    [← Back] [Download]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Resume Builder                                          │
│                                                              │
│  ┌──────────────────────────┐  ┌─────────────────────────┐ │
│  │  PDF PREVIEW             │  │  CONTROLS & AI EDITOR   │ │
│  │  ────────────────────    │  │  ─────────────────────  │ │
│  │                          │  │                         │ │
│  │  ┌────────────────────┐  │  │  📊 Resume Scores       │ │
│  │  │                    │  │  │  [Check Scores]         │ │
│  │  │   Resume PDF       │  │  │  ┌───────────────────┐ │ │
│  │  │   (Scrollable)     │  │  │  │ Score: 85/100    │ │ │
│  │  │                    │  │  │  │ [Progress bars]   │ │ │
│  │  │                    │  │  │  └───────────────────┘ │ │
│  │  │                    │  │  │                         │ │
│  │  └────────────────────┘  │  │  💬 AI Editor           │ │
│  │                          │  │  ┌───────────────────┐ │ │
│  │  [Upload File] [New]     │  │  │ Chat History      │ │ │
│  │  [Undo] [Redo]           │  │  │ You: Make it...   │ │ │
│  │                          │  │  │ AI: ✅ Done!      │ │ │
│  │                          │  │  └───────────────────┘ │ │
│  │                          │  │                         │ │
│  │                          │  │  📋 Job Description     │ │
│  │                          │  │  [Add/Edit JD]          │ │
│  │                          │  │                         │ │
│  │                          │  │  📑 Sections            │ │
│  │                          │  │  [@Experience] [@...]   │ │
│  │                          │  │                         │ │
│  │                          │  │  💭 Query               │ │
│  │                          │  │  [Type here...] [Send]  │ │
│  │                          │  │                         │ │
│  └──────────────────────────┘  └─────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Mobile Layout (Stacked):
┌─────────────────────┐
│  PDF Preview        │
│  [Full Screen]      │
├─────────────────────┤
│  Scores             │
│  [Expandable]       │
├─────────────────────┤
│  AI Editor          │
│  [Collapsible]      │
└─────────────────────┘
```

#### Document Generator Page (Resume/SOP/Cover Letter)

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] HireEdgeAI                    [Home] [Builder]      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🧰 Resume Generator                                        │
│  Fill in your details and let AI create your resume         │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  FORM (Multi-step or Single)                          │ │
│  │  ──────────────────────────────────────────────────   │ │
│  │                                                       │ │
│  │  Personal Information                                 │ │
│  │  Full Name* [____________]                            │ │
│  │  Email*     [____________]                            │ │
│  │  Phone      [____________]                            │ │
│  │                                                       │ │
│  │  Experience                                           │ │
│  │  Title      [____________]                            │ │
│  │  Company    [____________]                            │ │
│  │  ...                                                  │ │
│  │                                                       │ │
│  │  [⚡ Generate Preview]                                │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  PREVIEW (After generation)                           │ │
│  │  ──────────────────────────────────────────────────   │ │
│  │  Format: ( ) DOCX  (•) PDF                            │ │
│  │                                                       │ │
│  │  [Preview Content - Watermarked]                      │ │
│  │                                                       │ │
│  │  [⬇️ Download Preview]                                │ │
│  │                                                       │ │
│  │  [💳 Pay ₹XXX] (Razorpay Link)                        │ │
│  │                                                       │ │
│  │  ────────────────────────────────────────────────     │ │
│  │                                                       │ │
│  │  ✅ Unlock Final Document                             │ │
│  │  Payment ID: [pay_ABC123...]                         │ │
│  │  [Verify Payment]                                    │ │
│  │                                                       │ │
│  │  [⬇️ Download Final] (after verification)            │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 Component Structure

### Core UI Components (shadcn/ui)

- **Button**: Primary, secondary, outline, ghost variants
- **Input**: Text, textarea, with validation states
- **Card**: Container for sections
- **Dialog**: Modals for confirmations
- **Tabs**: Navigation between document types
- **Form**: Form wrapper with validation
- **Toast**: Success/error notifications
- **Skeleton**: Loading states
- **Progress**: Score displays

### Custom Components

1. **PDFPreview.tsx**
   - Embed PDF using `<iframe>` or `react-pdf`
   - Full-screen toggle
   - Zoom controls
   - Loading state

2. **ResumeScoring.tsx**
   - Tabbed interface (ATS Universal, HBPS, ATS with JD)
   - Progress bars for sub-scores
   - Color-coded scores (green/yellow/red)
   - Expandable recommendations

3. **AIChatInterface.tsx**
   - Scrollable chat history
   - Message bubbles (user/AI)
   - Input field with send button
   - Loading indicator during AI processing

4. **SectionButtons.tsx**
   - Grid of clickable section cards
   - Active state highlighting
   - Responsive grid (3 cols desktop, 2 tablet, 1 mobile)

5. **PaymentVerification.tsx**
   - Payment ID input
   - Verification status display
   - Success/error states
   - Download button (enabled after verification)

---

## 🔌 API Integration

### API Client Setup

```typescript
// lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor (add auth if needed)
apiClient.interceptors.request.use((config) => {
  // Add auth token if available
  return config;
});

// Response interceptor (error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    return Promise.reject(error);
  }
);
```

### API Functions

**Resume Builder APIs** (`lib/api/resume-builder.ts`)
- `createSession()` - Create new resume session
- `getSessionState()` - Get current session state
- `updateLatex()` - Update LaTeX content
- `compilePDF()` - Compile LaTeX to PDF
- `getPDF()` - Download PDF
- `getSections()` - Get parsed sections
- `editSection()` - AI edit section
- `chat()` - Send chat message
- `calculateScores()` - Calculate ATS/HBPS scores
- `uploadFile()` - Upload resume file
- `setJobDescription()` - Set JD for context

**Document Generator APIs** (`lib/api/document-generator.ts`)
- `generateResume()` - Generate resume from form
- `generateSOP()` - Generate SOP
- `generateCoverLetter()` - Generate cover letter
- `generateVisaCoverLetter()` - Generate visa cover letter
- `renderDocument()` - Render document (DOCX/PDF)
- `verifyPayment()` - Verify Razorpay payment

---

## 📄 Pages & Routes

### Route Structure

```
/                          → Landing page
/resume-builder            → Interactive Resume Builder
/resume                    → Resume Generator (form-based)
/sop                       → SOP Generator
/cover-letter              → Cover Letter Generator
/visa-cover-letter         → Visa Cover Letter Generator
```

### Page Components

1. **app/page.tsx** (Landing)
   - Hero section
   - Features grid
   - Pricing cards
   - Call-to-action

2. **app/resume-builder/page.tsx**
   - Two-column layout (PDF + Controls)
   - Session management
   - Real-time updates

3. **app/resume/page.tsx**
   - Multi-step form
   - Preview display
   - Payment flow

4. **app/sop/page.tsx**, **app/cover-letter/page.tsx**, **app/visa-cover-letter/page.tsx**
   - Similar structure to resume page
   - Form-specific fields

---

## 🗄️ State Management

### Zustand Stores

**resumeBuilderStore.ts**
```typescript
interface ResumeBuilderState {
  sessionId: string | null;
  latex: string;
  pdfUrl: string | null;
  selectedSection: string | null;
  chatHistory: ChatMessage[];
  jobDescription: string;
  scores: ResumeScores | null;
  
  // Actions
  createSession: () => Promise<void>;
  updateLatex: (latex: string) => Promise<void>;
  compilePDF: () => Promise<void>;
  // ... more actions
}
```

**sessionStore.ts** (for document generators)
```typescript
interface SessionState {
  currentStep: number;
  formData: Record<string, any>;
  previewData: any;
  paymentVerified: boolean;
  // ... more state
}
```

---

## 📝 Detailed Implementation Steps

### Phase 1: Foundation (Week 1)

#### Day 1-2: Project Setup
- [ ] Initialize Next.js project
- [ ] Install dependencies
- [ ] Setup shadcn/ui
- [ ] Configure Tailwind
- [ ] Setup project structure
- [ ] Configure environment variables

#### Day 3: Design System
- [ ] Define color palette
- [ ] Setup typography
- [ ] Create base UI components
- [ ] Setup theme configuration
- [ ] Create layout components (Header, Footer)

#### Day 4-5: Landing Page
- [ ] Build Hero section
- [ ] Create Features grid
- [ ] Add Pricing section
- [ ] Implement navigation
- [ ] Make responsive

### Phase 2: Resume Builder (Week 2)

#### Day 1-2: Core Components
- [ ] Create PDFPreview component
- [ ] Build API client for resume builder
- [ ] Implement session management
- [ ] Create Zustand store

#### Day 3: PDF & LaTeX Integration
- [ ] Implement PDF display (react-pdf or iframe)
- [ ] Setup LaTeX compilation flow
- [ ] Handle compilation errors
- [ ] Add loading states

#### Day 4: Scoring System
- [ ] Build ResumeScoring component
- [ ] Implement score API calls
- [ ] Create score visualization
- [ ] Add recommendations display

#### Day 5: AI Chat Interface
- [ ] Build AIChatInterface component
- [ ] Implement chat API integration
- [ ] Add message history
- [ ] Handle AI responses

### Phase 3: Section Editing (Week 2-3)

#### Day 1-2: Section Management
- [ ] Create SectionButtons component
- [ ] Implement section selection
- [ ] Build section editing flow
- [ ] Add section replace logic

#### Day 3: Job Description
- [ ] Create JobDescriptionInput component
- [ ] Implement JD storage
- [ ] Add JD context to AI requests

#### Day 4-5: File Operations
- [ ] Implement file upload
- [ ] Add file conversion handling
- [ ] Create download functionality (PDF/LaTeX)
- [ ] Add undo/redo

### Phase 4: Document Generators (Week 3-4)

#### Day 1-2: Resume Generator
- [ ] Create ResumeForm component
- [ ] Implement form validation (Zod)
- [ ] Build preview display
- [ ] Add format selector

#### Day 3: Payment Integration
- [ ] Create PaymentVerification component
- [ ] Integrate Razorpay payment links
- [ ] Implement payment verification API
- [ ] Add download after verification

#### Day 4-5: Other Document Types
- [ ] Create SopForm component
- [ ] Create CoverLetterForm component
- [ ] Create VisaCoverLetterForm component
- [ ] Reuse payment/download logic

### Phase 5: Polish & Optimization (Week 4-5)

#### Day 1-2: Responsive Design
- [ ] Test all pages on mobile
- [ ] Fix layout issues
- [ ] Optimize touch interactions
- [ ] Test on tablets

#### Day 3: Performance
- [ ] Optimize images
- [ ] Add code splitting
- [ ] Implement lazy loading
- [ ] Optimize API calls

#### Day 4: Error Handling
- [ ] Add error boundaries
- [ ] Implement error states
- [ ] Add retry logic
- [ ] User-friendly error messages

#### Day 5: Testing & QA
- [ ] Test all flows
- [ ] Fix bugs
- [ ] Accessibility audit
- [ ] Cross-browser testing

---

## 📱 Responsive Design Strategy

### Breakpoints

```css
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */
```

### Layout Strategies

**Resume Builder:**
- Desktop: Side-by-side (PDF left, Controls right)
- Tablet: Stacked (PDF top, Controls bottom)
- Mobile: Tabs or accordion (switch between PDF/Controls)

**Document Generators:**
- Desktop: Full-width form
- Tablet: Full-width, adjusted spacing
- Mobile: Single column, larger inputs

### Mobile Optimizations

1. **Touch Targets**: Minimum 44x44px
2. **Spacing**: Increased padding on mobile
3. **Typography**: Slightly larger fonts on mobile
4. **Forms**: Full-width inputs, larger buttons
5. **Navigation**: Hamburger menu on mobile
6. **PDF Preview**: Full-screen option on mobile

---

## ✨ Professional Polish

### Visual Enhancements

1. **Animations**
   - Smooth page transitions
   - Loading spinners
   - Success/error animations
   - Hover effects

2. **Micro-interactions**
   - Button press feedback
   - Form validation animations
   - Toast notifications
   - Progress indicators

3. **Loading States**
   - Skeleton screens
   - Progress bars
   - Loading spinners
   - Optimistic UI updates

### User Experience

1. **Feedback**
   - Clear success messages
   - Helpful error messages
   - Progress indicators
   - Confirmation dialogs

2. **Accessibility**
   - ARIA labels
   - Keyboard navigation
   - Focus management
   - Screen reader support

3. **Performance**
   - Fast initial load
   - Smooth interactions
   - Efficient API calls
   - Optimized images

### SEO & Meta

- Meta tags for each page
- Open Graph tags
- Twitter cards
- Structured data
- Sitemap
- robots.txt

---

## 🚀 Getting Started Checklist

- [ ] Step 1: Run project setup commands
- [ ] Step 2: Create folder structure
- [ ] Step 3: Setup API client
- [ ] Step 4: Create layout components
- [ ] Step 5: Build landing page
- [ ] Step 6: Implement Resume Builder
- [ ] Step 7: Build Document Generators
- [ ] Step 8: Add Payment Integration
- [ ] Step 9: Make responsive
- [ ] Step 10: Polish & deploy

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Validation](https://zod.dev/)
- [Zustand](https://github.com/pmndrs/zustand)

---

## 🔄 Migration Timeline

**Estimated Duration: 4-5 weeks**

- Week 1: Foundation & Landing Page
- Week 2: Resume Builder Core
- Week 3: Resume Builder Advanced + Document Generators Start
- Week 4: Document Generators Complete
- Week 5: Polish, Testing, Deployment

---

This plan ensures a professional, responsive, and feature-complete React/Next.js application that maintains all functionality from the Streamlit version while providing a modern, polished user experience.

