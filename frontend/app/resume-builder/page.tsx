'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { ArrowLeft, FileText, Send, Download, BarChart3, Menu } from 'lucide-react';
import { createSession, getPDF, compilePDF, calculateScores, getSections, uploadFile, getSessionState, downloadLaTeX, getJobDescription as getJobDescriptionAPI, setJobDescription as setJobDescriptionAPI, clearJobDescription } from '@/lib/api/resume-builder';
import { ResumeScores, Section } from '@/types';
import ResumeScoringModal from '@/components/resume/ResumeScoringModal';
import Sidebar from '@/components/ui/Sidebar';
import toast from 'react-hot-toast';

export default function ResumeBuilderPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [scores, setScores] = useState<ResumeScores | null>(null);
  const [isScoreModalOpen, setIsScoreModalOpen] = useState(false);
  const [isLoadingScores, setIsLoadingScores] = useState(false);
  const [sections, setSections] = useState<Section[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [versionInfo, setVersionInfo] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');
  const [jobDescriptionInput, setJobDescriptionInput] = useState<string>('');
  const pdfContainerRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await createSession();
        setSessionId(response.session_id);
        // Compile initial PDF
        await compileAndUpdate(response.session_id);
        // Load sections
        await loadSections(response.session_id);
        // Load job description if exists
        await loadJobDescription(response.session_id);
      } catch (error) {
        console.error('Failed to create session:', error);
        toast.error('Failed to initialize resume builder');
      }
    };
    initSession();
  }, []);

  const loadJobDescription = async (sid: string) => {
    try {
      const response = await getJobDescriptionAPI(sid);
      if (response.job_description) {
        setJobDescription(response.job_description);
        setJobDescriptionInput(response.job_description);
      }
    } catch (error) {
      console.error('Failed to load job description:', error);
    }
  };

  const handleSaveJobDescription = async () => {
    if (!sessionId) {
      toast.error('Session not initialized');
      return;
    }
    
    const wordCount = jobDescriptionInput.trim().split(/\s+/).filter(w => w).length;
    if (wordCount > 1000) {
      toast.error('Job description must be 1000 words or less');
      return;
    }
    
    try {
      const jdToSave = jobDescriptionInput.trim();
      console.log('Saving job description, sessionId:', sessionId);
      console.log('JD content length:', jdToSave.length);
      console.log('JD content preview:', jdToSave.substring(0, 100));
      
      if (!jdToSave) {
        toast.error('Job description cannot be empty');
        return;
      }
      
      const result = await setJobDescriptionAPI(sessionId, jdToSave);
      console.log('Save result:', result);
      
      // Small delay to ensure backend processed it
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verify it was saved
      const verify = await getJobDescriptionAPI(sessionId);
      console.log('Verified JD in session:', verify);
      console.log('JD present:', verify.job_description ? `Yes (${verify.job_description.length} chars)` : 'No');
      
      if (verify.job_description && verify.job_description.trim()) {
        setJobDescription(verify.job_description);
        setJobDescriptionInput(verify.job_description);
        toast.success('Job description saved successfully');
      } else {
        console.error('JD verification failed - JD is empty or not present');
        toast.error('Job description save verification failed - please try again');
      }
    } catch (error: any) {
      console.error('Failed to save job description:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      console.error('Error message:', error.message);
      toast.error(`Failed to save job description: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
    }
  };

  const handleClearJobDescription = async () => {
    if (!sessionId) return;
    
    try {
      await clearJobDescription(sessionId);
      setJobDescription('');
      setJobDescriptionInput('');
      toast.success('Job description cleared');
    } catch (error) {
      console.error('Failed to clear job description:', error);
      toast.error('Failed to clear job description');
    }
  };

  const loadSections = async (sid: string) => {
    try {
      const response = await getSections(sid);
      if (response.sections) {
        setSections(response.sections);
      }
    } catch (error) {
      console.error('Failed to load sections:', error);
    }
  };

  const compileAndUpdate = async (sid: string) => {
    setIsCompiling(true);
    try {
      console.log('Compiling PDF for session:', sid);
      const compileResult = await compilePDF(sid);
      console.log('Compile result:', compileResult);
      
      if (!compileResult.success) {
        throw new Error(compileResult.error || 'Compilation failed');
      }
      
      const pdfBlob = await getPDF(sid);
      const url = URL.createObjectURL(pdfBlob);
      setPdfUrl(url);
      console.log('PDF compiled and loaded successfully');
    } catch (error: any) {
      console.error('Failed to compile PDF:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to compile PDF';
      toast.error(`Compilation failed: ${errorMessage}`);
    } finally {
      setIsCompiling(false);
    }
  };

  const handleCheckScores = async () => {
    if (!sessionId) return;
    
    setIsLoadingScores(true);
    setIsScoreModalOpen(true);
    
    try {
      // Debug: Check if JD is saved
      const jdCheck = await getJobDescriptionAPI(sessionId);
      console.log('Job description in session:', jdCheck.job_description ? `Present (${jdCheck.job_description.length} chars)` : 'Not present');
      
      const scoreData = await calculateScores(sessionId);
      console.log('Score data received:', JSON.stringify(scoreData, null, 2)); // Debug log
      console.log('ATS JD score:', scoreData.ats_jd ? 'Present' : 'Not present'); // Debug ATS JD
      setScores(scoreData);
    } catch (error) {
      console.error('Failed to calculate scores:', error);
      toast.error('Failed to calculate scores');
    } finally {
      setIsLoadingScores(false);
    }
  };

  const handleDownload = async () => {
    if (!sessionId) return;
    
    try {
      const pdfBlob = await getPDF(sessionId);
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'resume.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Resume downloaded');
    } catch (error) {
      console.error('Failed to download PDF:', error);
      toast.error('Failed to download PDF');
    }
  };

  const handleDownloadLaTeX = async () => {
    if (!sessionId) return;
    
    try {
      const latexBlob = await downloadLaTeX(sessionId);
      const url = URL.createObjectURL(latexBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'resume.tex';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('LaTeX downloaded');
    } catch (error) {
      console.error('Failed to download LaTeX:', error);
      toast.error('Failed to download LaTeX');
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!sessionId) {
      toast.error('Session not initialized');
      return;
    }
    
    try {
      console.log('Uploading file:', file.name, 'Size:', file.size, 'bytes');
      const result = await uploadFile(sessionId, file);
      console.log('Upload result:', result);
      
      if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach((warning: string) => {
          toast(warning, { icon: '⚠️' });
        });
      }
      
      toast.success(`File ${file.name} uploaded successfully`);
      setIsSidebarOpen(false);
      // Reload sections and recompile
      await loadSections(sessionId);
      await compileAndUpdate(sessionId);
    } catch (error: any) {
      console.error('Failed to upload file:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload file';
      toast.error(`Upload failed: ${errorMessage}`);
    }
  };

  // Load session state for undo/redo
  useEffect(() => {
    const loadSessionState = async () => {
      if (!sessionId) return;
      try {
        const state = await getSessionState(sessionId);
        // Update undo/redo state if available in response
        // This depends on your backend response structure
      } catch (error) {
        console.error('Failed to load session state:', error);
      }
    };
    loadSessionState();
  }, [sessionId]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5 text-gray-600" />
          </button>
          <Link
            href="/"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </Link>
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Resume Builder</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCheckScores}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <BarChart3 className="h-4 w-4" />
            Check Scores
          </button>
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Download PDF"
          >
            <Download className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </header>

      {/* Main Content - Two Columns */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left: PDF Preview */}
        <div className="flex-1 bg-white border-r border-gray-200 flex flex-col min-w-0 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex-shrink-0">
            <h2 className="text-lg font-semibold text-gray-900">Resume Preview</h2>
          </div>
          <div className="flex-1 overflow-auto p-4 min-h-0">
            {isCompiling ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Compiling PDF...</p>
                </div>
              </div>
            ) : pdfUrl ? (
              <iframe
                src={pdfUrl}
                className="w-full h-full min-h-[600px] border border-gray-300 rounded-lg"
                title="Resume Preview"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Your resume preview will appear here</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: AI Editor */}
        <div className="w-96 bg-white flex flex-col flex-shrink-0 border-l border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex-shrink-0">
            <h2 className="text-lg font-semibold text-gray-900">AI Editor</h2>
          </div>

          {/* Chat History - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
            <div className="text-sm text-gray-500 text-center py-4">
              Your conversation will appear here...
            </div>
          </div>

          {/* Job Description Section */}
          <div className="border-t border-gray-200 p-4 flex-shrink-0">
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                {jobDescription ? '📋 Job Description ✓' : '📋 Add Job Description (optional)'}
              </summary>
              <div className="mt-2 space-y-2">
                <textarea
                  value={jobDescriptionInput}
                  onChange={(e) => setJobDescriptionInput(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none bg-gray-900 text-white placeholder-gray-400"
                  rows={3}
                  placeholder="Paste job description here to tailor your resume..."
                  maxLength={5000}
                />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {jobDescriptionInput.trim().split(/\s+/).filter(w => w).length}/1000 words
                  </span>
                  <div className="flex gap-2">
                    {jobDescription && (
                      <button
                        onClick={handleClearJobDescription}
                        className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 rounded transition-colors"
                      >
                        🗑️ Clear
                      </button>
                    )}
                    <button
                      onClick={handleSaveJobDescription}
                      className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                    >
                      💾 Save
                    </button>
                  </div>
                </div>
              </div>
            </details>
          </div>

          {/* Section Buttons */}
          <div className="border-t border-gray-200 p-4 flex-shrink-0 overflow-y-auto max-h-48">
            <p className="text-xs text-gray-500 mb-2">📑 Click section to edit:</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setChatMessage('@Full Resume: ')}
                className="px-3 py-2 text-xs bg-gray-900 hover:bg-gray-800 text-white rounded-lg transition-colors font-medium"
              >
                @Full Resume
              </button>
              {sections.length > 0 ? (
                sections.slice(0, 8).map((section, idx) => (
                  <button
                    key={idx}
                    onClick={() => setChatMessage(`@${section.name}: `)}
                    className="px-3 py-2 text-xs bg-gray-900 hover:bg-gray-800 text-white rounded-lg transition-colors truncate"
                    title={section.name}
                  >
                    @{section.name.length > 12 ? section.name.substring(0, 10) + '..' : section.name}
                  </button>
                ))
              ) : (
                <div className="col-span-2 text-xs text-gray-400 text-center py-2">
                  Loading sections...
                </div>
              )}
            </div>
          </div>

          {/* Query Input */}
          <div className="border-t border-gray-200 p-4 flex-shrink-0">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Type your request here..."
                className="flex-1 px-3 py-2 bg-gray-900 text-white border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    // Handle send
                  }
                }}
              />
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                title="Send"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              ⚠️ Set OPENAI_API_KEY to enable AI
            </p>
          </div>
        </div>
      </div>

      {/* Resume Scoring Modal */}
      <ResumeScoringModal
        isOpen={isScoreModalOpen}
        onClose={() => setIsScoreModalOpen(false)}
        scores={scores}
        isLoading={isLoadingScores}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onUpload={handleFileUpload}
        onUndo={() => toast('Undo not yet implemented')}
        onRedo={() => toast('Redo not yet implemented')}
        onDownloadPDF={handleDownload}
        onDownloadLaTeX={handleDownloadLaTeX}
        canUndo={canUndo}
        canRedo={canRedo}
        versionInfo={versionInfo}
      />
    </div>
  );
}

