import axios from "axios";
import { useEffect, useRef, useState } from "react";

const navigation = ["Dashboard", "Resume", "Job matching", "Mock interview", "History"];

function App() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "";
  const fileInput = useRef(null);
  const [apiStatus, setApiStatus] = useState("Checking API...");
  const [resume, setResume] = useState(null);
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const [jobText, setJobText] = useState("");
  const [job, setJob] = useState(null);
  const [match, setMatch] = useState(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    axios
      .get(`${apiBaseUrl}/health`)
      .then(() => setApiStatus("API connected"))
      .catch(() => setApiStatus("API unavailable"));
  }, [apiBaseUrl]);

  const request = async (label, action) => {
    setBusy(label);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The request could not be completed.");
    } finally {
      setBusy("");
    }
  };

  const uploadResume = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    request("upload", async () => {
      const formData = new FormData();
      formData.append("file", file);
      const response = await axios.post(`${apiBaseUrl}/api/v1/resumes/upload`, formData);
      setResume(response.data);
      setResumeAnalysis(null);
      setMatch(null);
      setMessage("Resume uploaded and text extracted.");
    });
  };

  const analyzeResume = () => {
    if (!resume) return;
    request("resume", async () => {
      const response = await axios.post(`${apiBaseUrl}/api/v1/resumes/${resume.id}/analyze`);
      setResumeAnalysis(response.data);
      setMessage("Resume analysis is ready.");
    });
  };

  const analyzeJob = () => {
    request("job", async () => {
      const response = await axios.post(`${apiBaseUrl}/api/v1/jobs/analyze`, {
        description: jobText,
      });
      setJob(response.data);
      setMatch(null);
      setMessage("Job description analysis is ready.");
    });
  };

  const matchResume = () => {
    if (!resume || !job) return;
    request("match", async () => {
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/jobs/${job.id}/match/${resume.id}`,
      );
      setMatch(response.data);
      setMessage("Resume-to-job match is ready.");
    });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">IQ</span>
          <span>Interview<span className="brand-accent">IQ</span></span>
        </div>
        <p className="eyebrow">Workspace</p>
        <nav>
          {navigation.map((item, index) => (
            <button className={`nav-item ${index === 0 ? "active" : ""}`} key={item}>
              <span className="nav-icon">{["⌂", "↥", "◎", "◉", "▤"][index]}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="avatar">AP</div>
          <div><strong>Alex Parker</strong><span>Candidate</span></div>
          <span className="more">•••</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">AI preparation workspace</p>
            <h1>Good morning, Alex <span aria-hidden="true">✦</span></h1>
          </div>
          <span className={`status-pill ${apiStatus === "API connected" ? "online" : ""}`}>
            <span className="status-dot" /> {apiStatus}
          </span>
        </header>

        <section className="hero-card">
          <div>
            <p className="eyebrow cyan">Phase 3 intelligence</p>
            <h2>Turn your experience into a focused preparation plan.</h2>
            <p className="hero-copy">
              Analyze your resume, compare it with a target role, and get evidence-based recommendations.
            </p>
            <button className="primary-button" onClick={() => fileInput.current?.click()}>
              {resume ? "Replace resume" : "Upload resume"} <span>→</span>
            </button>
            <input ref={fileInput} hidden type="file" accept=".pdf,.docx" onChange={uploadResume} />
          </div>
          <div className="hero-orbit" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-core">✦</div></div>
        </section>

        {(message || error) && <div className={`notice ${error ? "error" : "success"}`}>{error || message}</div>}

        <section className="analysis-grid">
          <article className="panel workflow-panel">
            <div className="panel-heading"><div><p className="eyebrow">Resume intelligence</p><h3>{resume?.original_filename || "No resume uploaded"}</h3></div></div>
            <p className="muted">{resume ? "Text extracted successfully. Run an evidence-based analysis." : "Upload a PDF or DOCX resume to begin."}</p>
            <button className="secondary-button" disabled={!resume || busy === "resume"} onClick={analyzeResume}>
              {busy === "resume" ? "Analyzing..." : "Analyze resume"} <span>→</span>
            </button>
            {resumeAnalysis && <AnalysisDetails analysis={resumeAnalysis} />}
          </article>

          <article className="panel workflow-panel">
            <div className="panel-heading"><div><p className="eyebrow">Target role</p><h3>Job description</h3></div></div>
            <textarea className="job-input" value={jobText} onChange={(event) => setJobText(event.target.value)} placeholder="Paste the job description here..." />
            <button className="secondary-button" disabled={jobText.trim().length < 20 || busy === "job"} onClick={analyzeJob}>
              {busy === "job" ? "Analyzing..." : "Analyze job description"} <span>→</span>
            </button>
            {job && <JobDetails job={job} />}
          </article>
        </section>

        <section className="panel match-panel">
          <div className="panel-heading"><div><p className="eyebrow">Evidence-based comparison</p><h3>Resume-to-job match</h3></div></div>
          <button className="primary-button" disabled={!resumeAnalysis || !job || busy === "match"} onClick={matchResume}>
            {busy === "match" ? "Matching..." : "Match resume"} <span>→</span>
          </button>
          {match && <MatchDetails match={match} />}
        </section>
      </main>
    </div>
  );
}

function AnalysisDetails({ analysis }) {
  return <div className="details"><p>{analysis.professional_summary || "No professional summary was identified."}</p><TagList title="Technical skills" items={analysis.technical_skills} /><TagList title="Strengths" items={analysis.strengths} /><TagList title="Areas for improvement" items={analysis.areas_for_improvement} /></div>;
}

function JobDetails({ job }) {
  return <div className="details"><p>{job.summary || "No summary was identified."}</p><TagList title="Required skills" items={job.required_technical_skills} /><TagList title="Preferred skills" items={job.preferred_skills} /></div>;
}

function MatchDetails({ match }) {
  return <div className="match-result"><div className="score"><strong>{match.overall_match_score}</strong><span>/ 100</span></div><p>{match.score_explanation}</p><TagList title="Matching skills" items={match.matching_skills} /><TagList title="Missing skills" items={match.missing_skills} /><TagList title="Preparation recommendations" items={match.personalized_preparation_recommendations} /></div>;
}

function TagList({ title, items = [] }) {
  return <div className="tag-group"><strong>{title}</strong>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <span className="muted">None identified</span>}</div>;
}

export default App;
