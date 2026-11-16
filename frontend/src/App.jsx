import React, { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [jdTitle, setJdTitle] = useState('Senior Java & Microservices Backend Engineer');
  const [jdText, setJdText] = useState(
`Job Title: Senior Java & Microservices Backend Engineer
Experience Required: 4+ years of professional experience
Required Qualification: B.Tech / B.E. / M.Tech / MCA in Computer Science or Engineering

Role Overview:
We are looking for a Backend Engineer with strong hands-on expertise in Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, and Docker to architect and scale high-throughput distributed backend services.`
  );
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [jdParsed, setJdParsed] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [activeCandidate, setActiveCandidate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleLoadSampleBatch = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/demo/load-sample-batch`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to load sample batch from backend.');
      const data = await res.json();
      setJdParsed(data.jd);
      setRankings(data.rankings);
      if (data.rankings.length > 0) setActiveCandidate(data.rankings[0]);
    } catch (err) {
      setErrorMsg(err.message || 'Ensure FastAPI backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateBatch = async (e) => {
    e.preventDefault();
    if (!jdText.trim()) {
      setErrorMsg('Please enter a Job Description first.');
      return;
    }
    if (selectedFiles.length === 0) {
      setErrorMsg('Please select at least 1 PDF/DOCX resume (10+ supported) or click "Load 12 Synthetic Resumes".');
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      const jdRes = await fetch(`${API_BASE}/api/jd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: jdTitle, raw_text: jdText }),
      });
      if (!jdRes.ok) throw new Error('Failed to parse Job Description.');
      const jdObj = await jdRes.json();

      const formData = new FormData();
      formData.append('jd_id', jdObj.jd_id);
      Array.from(selectedFiles).forEach((file) => formData.append('files', file));

      const evalRes = await fetch(`${API_BASE}/api/resumes/evaluate`, {
        method: 'POST',
        body: formData,
      });
      if (!evalRes.ok) throw new Error('Failed to evaluate uploaded resumes.');
      const evalData = await evalRes.json();
      setJdParsed(evalData.jd);
      setRankings(evalData.rankings);
      if (evalData.rankings.length > 0) setActiveCandidate(evalData.rankings[0]);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">AI-Based Resume Matching & Candidate Ranking System</h1>
            <p className="text-sm text-slate-400">FastAPI + Sentence Transformers (all-MiniLM-L6-v2) + Hybrid Semantic Scoring</p>
          </div>
          <button
            onClick={handleLoadSampleBatch}
            disabled={loading}
            className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold text-white transition"
          >
            {loading ? 'Processing Batch...' : 'Load 12 Synthetic Resumes (Sample Batch)'}
          </button>
        </header>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-950/70 border border-rose-700 text-rose-200 text-sm">
            {errorMsg}
          </div>
        )}

        {/* Modules 1 & 2: JD Input + Batch Resume Upload */}
        <form onSubmit={handleEvaluateBatch} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h2 className="text-base font-semibold text-indigo-400">Module 1: Job Description Input</h2>
            <input
              type="text"
              value={jdTitle}
              onChange={(e) => setJdTitle(e.target.value)}
              placeholder="Job Role Title"
              className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm text-slate-100"
            />
            <textarea
              rows={6}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste Job Description here..."
              className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 text-sm text-slate-200 font-mono"
            />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-indigo-400">Module 2: Batch Resume Upload (PDF & DOCX, 10+ Files)</h2>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt"
                onChange={(e) => setSelectedFiles(e.target.files)}
                className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-slate-800 file:text-indigo-300 hover:file:bg-slate-700"
              />
              <p className="text-xs text-slate-400">
                Selected files: <span className="font-semibold text-slate-200">{selectedFiles.length}</span> (Supports batch upload of 10+ PDF and DOCX resumes)
              </p>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition"
            >
              {loading ? 'Analyzing & Ranking Resumes...' : 'Parse & Rank Uploaded Resumes'}
            </button>
          </div>
        </form>

        {/* Modules 4 & 5: Candidate Ranking Table + Candidate-Level Analysis */}
        {rankings.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h2 className="text-base font-semibold text-white">Module 4: Candidate Ranking Dashboard ({rankings.length} Candidates)</h2>
                <span className="text-xs text-slate-400">Click any row for Module 5 drill-down</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <th className="py-3 px-4">Rank</th>
                      <th className="py-3 px-4">Candidate</th>
                      <th className="py-3 px-4">Experience</th>
                      <th className="py-3 px-4">Match %</th>
                      <th className="py-3 px-4">Matched Skills</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.map((cand) => (
                      <tr
                        key={cand.id}
                        onClick={() => setActiveCandidate(cand)}
                        className={`border-b border-slate-800/70 cursor-pointer transition ${
                          activeCandidate?.id === cand.id ? 'bg-indigo-950/40' : 'hover:bg-slate-800/40'
                        }`}
                      >
                        <td className="py-3 px-4 font-mono text-xs text-slate-400">#{cand.rank}</td>
                        <td className="py-3 px-4 font-medium text-white">
                          {cand.candidate_name}
                          <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{cand.file_format}</span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">{cand.experience_years} years</td>
                        <td className="py-3 px-4 font-bold text-emerald-400">{cand.overall_score}%</td>
                        <td className="py-3 px-4 text-xs text-slate-300">{cand.matched_skills.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {activeCandidate && (
              <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-indigo-400 font-semibold">Module 5: Candidate-Level Analysis</span>
                    <h3 className="text-xl font-bold text-white mt-0.5">{activeCandidate.candidate_name}</h3>
                    <p className="text-xs text-slate-400">{activeCandidate.email} • {activeCandidate.phone}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{activeCandidate.education_summary}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-extrabold text-emerald-400">{activeCandidate.overall_score}%</span>
                    <p className="text-xs text-slate-400">Overall Match</p>
                  </div>
                </div>

                <div className="text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <strong className="text-slate-200">Experience Comparison:</strong>{' '}
                  <span className="text-slate-300">{activeCandidate.experience_status}</span>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1.5">Matched Skills (Exact & Semantic)</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {activeCandidate.matched_skills.map((s, idx) => (
                      <span key={idx} className="px-2 py-1 text-xs rounded bg-emerald-950/80 border border-emerald-800 text-emerald-200">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-400 mb-1.5">Missing Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {activeCandidate.missing_skills.length > 0 ? (
                      activeCandidate.missing_skills.map((s, idx) => (
                        <span key={idx} className="px-2 py-1 text-xs rounded bg-rose-950/80 border border-rose-800 text-rose-200">
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400">None — All required skills covered!</span>
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-1.5">Reasons Behind the Matching Score</h4>
                  <ul className="space-y-1.5 text-xs text-slate-300 list-disc pl-4">
                    {activeCandidate.reasons.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
