// Resume Builder Types
export interface ResumeSession {
  sessionId: string;
  latex: string;
  pdfUrl?: string;
}

export interface Section {
  name: string;
  content: string;
  type?: string;
  start_line?: number;
  end_line?: number;
  preview?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ResumeScores {
  ats_universal?: {
    score: number;
    rating: string;
    summary: string;
    section_score: number;
    metrics_score: number;
    action_verbs_score: number;
    structure_score: number;
    design_score: number;
    metrics_count: number;
    action_verbs_count: number;
    word_count: number;
    found_sections: string[];
    missing_sections: string[];
    design_issues: string[];
    recommendations: string[];
  };
  hbps?: {
    score: number;
    rating: string;
    summary: string;
    first_impression_score: number;
    scannability_score: number;
    impact_numbers_score: number;
    credibility_score: number;
    clarity_score: number;
    what_recruiter_sees: string[];
    recommendations: string[];
  };
  ats_jd?: {
    score: number;
    rating: string;
    summary: string;
    matched_keywords: string[];
    missing_keywords: string[];
  };
}

