'use client';

import { ResumeScores } from '@/types';
import Modal from '../ui/Modal';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';

interface ResumeScoringModalProps {
  isOpen: boolean;
  onClose: () => void;
  scores: ResumeScores | null;
  isLoading?: boolean;
}

export default function ResumeScoringModal({
  isOpen,
  onClose,
  scores,
  isLoading,
}: ResumeScoringModalProps) {
  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-green-500';
    if (score >= 55) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRatingEmoji = (rating: string) => {
    const ratingLower = rating.toLowerCase();
    if (ratingLower.includes('excellent')) return '🌟';
    if (ratingLower.includes('good')) return '✅';
    if (ratingLower.includes('fair')) return '⚠️';
    return '❌';
  };

  const renderATSUniversal = () => {
    if (!scores?.ats_universal) return null;
    const ats = scores.ats_universal;
    return (
      <div className="border border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">📊 ATS Universal Score</h3>
        <p className="text-sm text-gray-600 mb-4">Measures ATS compatibility without a job description</p>
        
        <div className="text-center mb-6">
          <div className={`text-5xl font-bold ${getScoreColor(ats.score)}`}>
            {ats.score}
            <span className="text-2xl text-gray-400">/100</span>
          </div>
          <div className="text-lg font-semibold text-gray-700 mt-2">
            {getRatingEmoji(ats.rating)} {ats.rating}
          </div>
          <p className="text-sm text-gray-600 mt-2">{ats.summary}</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Sections</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${ats.section_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">{ats.section_score}/100</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Metrics</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${ats.metrics_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">
              {ats.metrics_score}/100 ({ats.metrics_count} found)
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Action Verbs</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${ats.action_verbs_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">
              {ats.action_verbs_score}/100 ({ats.action_verbs_count} found)
            </div>
          </div>
        </div>

        {ats.found_sections && ats.found_sections.length > 0 && (
          <div className="mb-2">
            <span className="text-sm font-medium text-green-700">
              ✅ Found: {ats.found_sections.join(', ')}
            </span>
          </div>
        )}
        {ats.missing_sections && ats.missing_sections.length > 0 && (
          <div className="mb-2">
            <span className="text-sm font-medium text-red-700">
              ❌ Missing: {ats.missing_sections.join(', ')}
            </span>
          </div>
        )}
        {ats.recommendations && ats.recommendations.length > 0 && (
          <div className="mt-4">
            <div className="text-sm font-semibold text-gray-900 mb-2">💡 Recommendations:</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {ats.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderHBPS = () => {
    if (!scores?.hbps) return null;
    const hbps = scores.hbps;
    return (
      <div className="border border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">🎯 HBPS Score (Human Best Practice)</h3>
        <p className="text-sm text-gray-600 mb-4">Measures what recruiters see in a 6-second scan</p>
        
        <div className="text-center mb-6">
          <div className={`text-5xl font-bold ${getScoreColor(hbps.score)}`}>
            {hbps.score}
            <span className="text-2xl text-gray-400">/100</span>
          </div>
          <div className="text-lg font-semibold text-gray-700 mt-2">
            {getRatingEmoji(hbps.rating)} {hbps.rating}
          </div>
          <p className="text-sm text-gray-600 mt-2">{hbps.summary}</p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">First Impression</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${hbps.first_impression_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">{hbps.first_impression_score}/100</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Scannability</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${hbps.scannability_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">{hbps.scannability_score}/100</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Impact Numbers</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${hbps.impact_numbers_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">{hbps.impact_numbers_score}/100</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Credibility</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${hbps.credibility_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1">{hbps.credibility_score}/100</div>
          </div>
        </div>

        {hbps.what_recruiter_sees && hbps.what_recruiter_sees.length > 0 && (
          <div className="mt-4">
            <div className="text-sm font-semibold text-gray-900 mb-2">👁️ What Recruiter Sees (in 6 seconds):</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {hbps.what_recruiter_sees.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {hbps.recommendations && hbps.recommendations.length > 0 && (
          <div className="mt-4">
            <div className="text-sm font-semibold text-gray-900 mb-2">💡 Recommendations:</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {hbps.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderATSJD = () => {
    if (!scores?.ats_jd) return null;
    const atsJd = scores.ats_jd;
    return (
      <div className="border border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">🎯 ATS Score (with Job Description)</h3>
        <p className="text-sm text-gray-600 mb-4">Measures how well your resume matches the job description</p>
        
        <div className="text-center mb-6">
          <div className={`text-5xl font-bold ${getScoreColor(atsJd.score)}`}>
            {atsJd.score}
            <span className="text-2xl text-gray-400">/100</span>
          </div>
          <div className="text-lg font-semibold text-gray-700 mt-2">
            {getRatingEmoji(atsJd.rating)} {atsJd.rating}
          </div>
          <p className="text-sm text-gray-600 mt-2">{atsJd.summary}</p>
        </div>

        {atsJd.matched_keywords && atsJd.matched_keywords.length > 0 && (
          <div className="mb-4">
            <div className="text-sm font-semibold text-green-700 mb-2">
              ✅ Matched Keywords:
            </div>
            <div className="flex flex-wrap gap-2">
              {atsJd.matched_keywords.slice(0, 15).map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
        {atsJd.missing_keywords && atsJd.missing_keywords.length > 0 && (
          <div>
            <div className="text-sm font-semibold text-red-700 mb-2">
              ❌ Missing Keywords:
            </div>
            <div className="flex flex-wrap gap-2">
              {atsJd.missing_keywords.slice(0, 10).map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Determine which tabs to show
  const tabs = [];
  if (scores?.ats_universal) tabs.push({ id: 'ats', label: 'ATS Universal' });
  if (scores?.hbps) tabs.push({ id: 'hbps', label: 'HBPS' });
  if (scores?.ats_jd) tabs.push({ id: 'ats_jd', label: 'ATS (with JD)' });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Resume Scores">
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : scores && tabs.length > 0 ? (
        tabs.length > 1 ? (
          // Multiple scores - use tabs
          <Tabs defaultValue={tabs[0].id}>
            <TabsList className="mb-6">
              {tabs.map((tab) => (
                <TabsTrigger key={tab.id} value={tab.id}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {scores.ats_universal && (
              <TabsContent value="ats">{renderATSUniversal()}</TabsContent>
            )}
            {scores.hbps && (
              <TabsContent value="hbps">{renderHBPS()}</TabsContent>
            )}
            {scores.ats_jd && (
              <TabsContent value="ats_jd">{renderATSJD()}</TabsContent>
            )}
          </Tabs>
        ) : (
          // Single score - no tabs
          <div>
            {scores.ats_universal && renderATSUniversal()}
            {scores.hbps && renderHBPS()}
            {scores.ats_jd && renderATSJD()}
          </div>
        )
      ) : (
        <div className="text-center py-12 text-gray-500">
          No scores available. Click "Check Scores" to analyze your resume.
        </div>
      )}
    </Modal>
  );
}
