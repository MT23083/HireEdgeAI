'use client';

import { X, Upload, RotateCcw, RotateCw, Download, FileText } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload?: (file: File) => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onDownloadPDF?: () => void;
  onDownloadLaTeX?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
  versionInfo?: string;
}

export default function Sidebar({
  isOpen,
  onClose,
  onUpload,
  onUndo,
  onRedo,
  onDownloadPDF,
  onDownloadLaTeX,
  canUndo = false,
  canRedo = false,
  versionInfo,
}: SidebarProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="fixed top-0 left-0 h-full w-80 bg-gray-900 text-white z-50 shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold">📁 Options</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* File Upload */}
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-300">
              Upload Resume
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".tex,.pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors border border-gray-700"
              >
                <Upload className="h-4 w-4" />
                <span className="text-sm">Choose File</span>
              </label>
            </div>
            <p className="text-xs text-gray-400 mt-1">Supports .tex, .pdf, .docx</p>
          </div>

          {/* New Resume Button */}
          <button
            className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-center gap-2"
            onClick={() => window.location.reload()}
          >
            <FileText className="h-4 w-4" />
            <span>🆕 New</span>
          </button>

          {/* Divider */}
          <div className="border-t border-gray-700" />

          {/* Undo/Redo */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={onUndo}
              disabled={!canUndo}
              className="px-4 py-3 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center justify-center gap-2"
              title="Undo"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
            <button
              onClick={onRedo}
              disabled={!canRedo}
              className="px-4 py-3 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center justify-center gap-2"
              title="Redo"
            >
              <RotateCw className="h-4 w-4" />
            </button>
          </div>

          {/* Version Info */}
          {versionInfo && (
            <p className="text-xs text-gray-400 text-center">{versionInfo}</p>
          )}

          {/* Divider */}
          <div className="border-t border-gray-700" />

          {/* Downloads */}
          <div className="space-y-2">
            {onDownloadPDF && (
              <button
                onClick={onDownloadPDF}
                className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Download className="h-4 w-4" />
                <span>⬇️ PDF</span>
              </button>
            )}
            {onDownloadLaTeX && (
              <button
                onClick={onDownloadLaTeX}
                className="w-full px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Download className="h-4 w-4" />
                <span>⬇️ LaTeX</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

