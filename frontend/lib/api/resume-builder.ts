import { apiClient } from './client';
import { ResumeScores } from '@/types';

// Session Management
export const createSession = async (defaultLatex?: string) => {
  const response = await apiClient.post('/api/resume/session/create', {
    default_latex: defaultLatex,
  });
  return response.data;
};

export const getSessionState = async (sessionId: string) => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/state`);
  return response.data;
};

export const updateLatex = async (sessionId: string, latex: string) => {
  const response = await apiClient.put(`/api/resume/session/${sessionId}/latex`, {
    latex_content: latex,
  });
  return response.data;
};

export const compilePDF = async (sessionId: string) => {
  const response = await apiClient.post(`/api/resume/session/${sessionId}/compile`);
  return response.data;
};

export const getPDF = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

// Sections
export const getSections = async (sessionId: string) => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/sections`);
  return response.data;
};

export const editSection = async (
  sessionId: string,
  sectionName: string,
  sectionContent: string,
  instruction: string
) => {
  const response = await apiClient.post(`/api/resume/session/${sessionId}/sections/edit`, {
    section_name: sectionName,
    section_content: sectionContent,
    user_instruction: instruction,
  });
  return response.data;
};

// Chat
export const sendChatMessage = async (
  sessionId: string,
  message: string,
  selectedSection?: string
) => {
  const response = await apiClient.post(`/api/resume/session/${sessionId}/chat`, {
    message,
    selected_section: selectedSection,
  });
  return response.data;
};

export const getChatHistory = async (sessionId: string, limit = 50) => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/chat/history`, {
    params: { limit },
  });
  return response.data;
};

// Scoring
export const calculateScores = async (
  sessionId: string
): Promise<ResumeScores> => {
  const response = await apiClient.post(`/api/resume/session/${sessionId}/score`, {});
  // Backend always returns ats_universal and hbps, and ats_jd if job_description is set in session
  return response.data;
};

// Job Description
export const setJobDescription = async (sessionId: string, jobDescription: string) => {
  try {
    const response = await apiClient.put(`/api/resume/session/${sessionId}/job-description`, {
      job_description: jobDescription,
    });
    console.log('setJobDescription - Full response:', response);
    console.log('setJobDescription - response.data:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('setJobDescription - Error:', error);
    console.error('setJobDescription - Error response:', error.response);
    throw error;
  }
};

export const getJobDescription = async (sessionId: string) => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/job-description`);
  return response.data;
};

export const clearJobDescription = async (sessionId: string) => {
  const response = await apiClient.delete(`/api/resume/session/${sessionId}/job-description`);
  return response.data;
};

// File Upload
export const uploadFile = async (sessionId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post(
    `/api/resume/session/${sessionId}/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

// Download LaTeX
export const downloadLaTeX = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(`/api/resume/session/${sessionId}/download/tex`, {
    responseType: 'blob',
  });
  return response.data;
};

