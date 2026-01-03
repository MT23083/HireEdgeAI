import Link from "next/link";
import { FileText, Sparkles, TrendingUp, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <FileText className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">HireEdgeAI</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/resume-builder"
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              >
                Resume Builder
              </Link>
              <Link
                href="/resume-builder"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 mb-6">
            Professional Resumes Made
            <span className="text-blue-600"> Effortless</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            AI-powered resume builder that helps you create ATS-friendly, professional resumes
            with real-time preview and intelligent suggestions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/resume-builder"
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
            >
              Start Building
            </Link>
            <button className="px-8 py-3 bg-white text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors border-2 border-gray-200">
              Watch Demo
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow">
            <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Sparkles className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">AI-Powered</h3>
            <p className="text-gray-600">
              Get intelligent suggestions and edits powered by advanced AI to improve your resume.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow">
            <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">ATS-Optimized</h3>
            <p className="text-gray-600">
              Built-in ATS scoring to ensure your resume passes applicant tracking systems.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow">
            <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Live Preview</h3>
            <p className="text-gray-600">
              See your resume in real-time as you make changes with instant PDF compilation.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow">
            <div className="bg-orange-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-orange-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Professional</h3>
            <p className="text-gray-600">
              Clean, modern templates that make your resume stand out to recruiters.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to build your resume?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Join thousands of professionals who have created their resumes with HireEdgeAI
          </p>
          <Link
            href="/resume-builder"
            className="inline-block px-8 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
          >
            Get Started for Free
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2025 HireEdgeAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
