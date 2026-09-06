import React, { useState } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle, ShieldAlert, FileText, ChevronRight } from 'lucide-react';

interface Evidence {
  text: string;
  source: string;
  label: string;
}

interface Claim {
  text: string;
  status: 'VERIFIED' | 'CONTRADICTORY' | 'UNVERIFIED';
  reason?: string;
  confidence: number;
  evidence: Evidence[];
}

interface VerificationReport {
  claims: Claim[];
  trust_score: number;
  raw_response: string;
}

function App() {
  const [query, setQuery] = useState('What is the role of Aspirin in acute viral infections?');
  const [responseText, setResponseText] = useState('Aspirin is completely safe to cure acute viral infections in infants.');
  const [report, setReport] = useState<VerificationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);

  const handleVerify = async () => {
    setLoading(true);
    setReport(null);
    setSelectedClaim(null);
    try {
      const response = await axios.post('http://localhost:8000/api/verify/', {
        query,
        response_text: responseText
      });
      setReport(response.data);
    } catch (error) {
      console.error('Verification failed', error);
      alert('Verification failed. Is the backend running?');
    }
    setLoading(false);
  };

  const handleGenerateAndVerify = async () => {
    setLoading(true);
    setReport(null);
    setSelectedClaim(null);
    try {
      const response = await axios.post('http://localhost:8000/api/generate-and-verify/', {
        query
      });
      setReport(response.data);
      setResponseText(response.data.raw_response);
    } catch (error) {
      console.error('Generation/Verification failed', error);
      alert('Verification failed. Is the backend running?');
    }
    setLoading(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 50) return 'text-amber-500';
    return 'text-red-500';
  };

  const getHighlightColor = (status: string) => {
    switch (status) {
      case 'VERIFIED': return 'bg-green-100 border-b-2 border-green-500';
      case 'CONTRADICTORY': return 'bg-red-100 border-b-2 border-red-500';
      case 'UNVERIFIED': return 'bg-amber-100 border-b-2 border-amber-500';
      default: return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col md:flex-row">
      {/* Left panel - Input */}
      <div className="w-full md:w-1/2 p-6 border-r border-gray-200 flex flex-col">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
          <ShieldAlert className="mr-2 text-blue-600" />
          Explainable Healthcare Verification
        </h1>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Medical Query</label>
          <input 
            type="text" 
            className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="mb-6 flex-grow flex flex-col">
          <label className="block text-sm font-medium text-gray-700 mb-1">AI Response to Verify</label>
          <textarea 
            className="w-full flex-grow p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            rows={8}
          />
        </div>

        <div className="flex space-x-3 mt-auto">
          <button 
            onClick={handleVerify}
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-md shadow transition disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Verify Response'}
          </button>
          
          <button 
            onClick={handleGenerateAndVerify}
            disabled={loading}
            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-md shadow transition disabled:opacity-50"
          >
            Auto-Generate & Verify
          </button>
        </div>
      </div>

      {/* Right panel - Verification View */}
      <div className="w-full md:w-1/2 p-6 bg-white relative">
        {!report && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <FileText size={64} className="mb-4 opacity-20" />
            <p>Enter a query and response to begin verification</p>
          </div>
        )}

        {loading && (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {report && (
          <div className="flex flex-col h-full">
            <div className="mb-8 flex items-center justify-between border-b pb-4">
              <h2 className="text-xl font-bold text-gray-800">Verification Report</h2>
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-500 mr-2">Trust Score:</span>
                <div className={`text-3xl font-extrabold ${getScoreColor(report.trust_score)}`}>
                  {report.trust_score.toFixed(0)}%
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Analyzed Response (Click sentences for explanation)</h3>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 leading-relaxed text-lg">
                {report.claims.map((claim, idx) => (
                  <span 
                    key={idx} 
                    className={`cursor-pointer transition-colors px-1 rounded ${getHighlightColor(claim.status)}`}
                    onClick={() => setSelectedClaim(claim)}
                  >
                    {claim.text}{' '}
                  </span>
                ))}
              </div>
            </div>

            {/* Explanation Drawer / Details */}
            {selectedClaim && (
              <div className="mt-auto bg-white border border-gray-200 shadow-lg rounded-lg p-5">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-gray-800 flex items-center">
                    {selectedClaim.status === 'VERIFIED' && <CheckCircle className="mr-2 text-green-500" size={20} />}
                    {selectedClaim.status === 'CONTRADICTORY' && <AlertCircle className="mr-2 text-red-500" size={20} />}
                    {selectedClaim.status === 'UNVERIFIED' && <AlertCircle className="mr-2 text-amber-500" size={20} />}
                    {selectedClaim.status}
                  </h3>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 font-mono">
                    Confidence: {(selectedClaim.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                
                {selectedClaim.reason && (
                  <div className="mb-4 bg-amber-50 p-2 rounded border border-amber-200 text-amber-800 text-sm font-medium flex items-center">
                    <AlertCircle size={16} className="mr-1" />
                    {selectedClaim.reason}
                  </div>
                )}
                
                <p className="text-gray-700 italic mb-4 border-l-4 border-gray-300 pl-3">
                  "{selectedClaim.text}"
                </p>

                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Retrieved Evidence</h4>
                {selectedClaim.evidence.length > 0 ? (
                  <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                    {selectedClaim.evidence.map((ev, i) => (
                      <div key={i} className="bg-gray-50 p-3 rounded text-sm border border-gray-100">
                        <p className="text-gray-800 mb-1">{ev.text}</p>
                        <p className="text-xs text-blue-600 font-medium">Source: {ev.source}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No relevant evidence found for this claim.</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
