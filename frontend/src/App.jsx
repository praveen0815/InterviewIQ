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
  const [question, setQuestion] = useState("");
  const [ragResult, setRagResult] = useState(null);
  const [interview, setInterview] = useState(null);
  const [interviewConfig, setInterviewConfig] = useState({
    interview_type: "Mixed",
    difficulty: "Intermediate",
    question_count: 5,
    duration_minutes: 30,
  });
  const [answer, setAnswer] = useState("");
  const [view, setView] = useState("workspace");
  const [dashboard, setDashboard] = useState(null);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    axios
      .get(`${apiBaseUrl}/health`)
      .then(() => setApiStatus("API connected"))
      .catch(() => setApiStatus("API unavailable"));
    axios.get(`${apiBaseUrl}/api/v1/dashboard/summary`).then((response) => setDashboard(response.data)).catch(() => {});
    axios.get(`${apiBaseUrl}/api/v1/reports?page=1&page_size=20`).then((response) => setReports(response.data.items)).catch(() => {});
  }, [apiBaseUrl]);

  const openReport = async (reportId) => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/v1/reports/${reportId}`);
      setSelectedReport(response.data);
      setView("report");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The report could not be loaded.");
    }
  };

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
      setRagResult(null);
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
      setRagResult(null);
      setMessage("Job description analysis is ready.");
    });
  };

  const askKnowledgeAssistant = () => {
    if (!resume || !question.trim()) return;
    request("rag", async () => {
      await axios.post(`${apiBaseUrl}/api/v1/rag/index/resume/${resume.id}`);
      if (job) await axios.post(`${apiBaseUrl}/api/v1/rag/index/job/${job.id}`);
      const response = await axios.post(`${apiBaseUrl}/api/v1/rag/query`, {
        resume_id: resume.id,
        job_id: job?.id,
        question: question.trim(),
      });
      setRagResult(response.data);
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

  const startInterview = () => {
    if (!resume || !resumeAnalysis || (job && !match)) return;
    request("interview-start", async () => {
      const response = await axios.post(`${apiBaseUrl}/api/v1/interviews/start`, {
        resume_id: resume.id,
        job_id: job?.id,
        ...interviewConfig,
      });
      setInterview(response.data);
      setAnswer("");
      setMessage("Interview started. Answer one question at a time.");
    });
  };

  const submitAnswer = () => {
    if (!interview || !answer.trim()) return;
    request("interview-answer", async () => {
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/interviews/${interview.id}/answer`,
        { answer: answer.trim() },
      );
      setInterview(response.data);
      setAnswer("");
    });
  };

  const completeInterview = () => {
    if (!interview) return;
    request("interview-complete", async () => {
      const response = await axios.post(`${apiBaseUrl}/api/v1/interviews/${interview.id}/complete`);
      setInterview(response.data);
      const reportResponse = await axios.get(`${apiBaseUrl}/api/v1/interviews/${interview.id}/report`);
      setSelectedReport(reportResponse.data);
      setView("report");
      setDashboard(null);
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
            <button className={`nav-item ${(item === "Dashboard" && view === "dashboard") || (item === "History" && view === "report") || (item === "Resume" && view === "workspace") ? "active" : ""}`} key={item} onClick={() => {
              if (item === "Dashboard") setView("dashboard");
              if (item === "History") setView("report");
              if (item === "Resume") setView("workspace");
            }}>
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

        {view === "dashboard" ? <DashboardView dashboard={dashboard} reports={reports} onOpenReport={openReport} /> : view === "report" ? <ReportView report={selectedReport} apiBaseUrl={apiBaseUrl} /> : <>
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

        <section className="panel assistant-panel">
          <div className="panel-heading"><div><p className="eyebrow cyan">Resume knowledge assistant</p><h3>Ask questions about your experience</h3></div></div>
          <p className="muted">Answers are grounded in your indexed resume{job ? " and target job description" : ""}.</p>
          <div className="assistant-form">
            <input
              className="job-input assistant-input"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="e.g. Which projects demonstrate API development?"
              onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); askKnowledgeAssistant(); } }}
            />
            <button className="primary-button" disabled={!resume || !question.trim() || busy === "rag"} onClick={askKnowledgeAssistant}>
              {busy === "rag" ? "Thinking..." : "Ask assistant"} <span>→</span>
            </button>
          </div>
          {ragResult && <div className="assistant-result">
            <p className="assistant-question"><strong>Your question:</strong> {question}</p>
            <p className="assistant-answer">{ragResult.answer}</p>
            <strong className="source-heading">Retrieved sources</strong>
            {ragResult.source_documents.length ? ragResult.source_documents.map((source, index) => (
              <span className="source-chip" key={`${source.source_type}-${source.source_id}-${index}`}>
                {source.source_type} · {source.filename || `#${source.source_id}`} · chunk {source.chunk_index}
              </span>
            )) : <span className="muted">No matching indexed sources were found.</span>}
          </div>}
        </section>

        <section className="panel interview-panel">
          <div className="panel-heading"><div><p className="eyebrow cyan">Phase 5 · LangGraph interview</p><h3>Personalized mock interview</h3></div></div>
          {!interview ? (
            <>
              <p className="muted">Uses your analyzed resume, job match, and retrieved context. Authentication is not yet implemented, so sessions are currently accessible by interview ID.</p>
              <div className="interview-config">
                <label>Interview type<select value={interviewConfig.interview_type} onChange={(event) => setInterviewConfig({ ...interviewConfig, interview_type: event.target.value })}><option>Technical</option><option>HR</option><option>Behavioral</option><option>Mixed</option></select></label>
                <label>Difficulty<select value={interviewConfig.difficulty} onChange={(event) => setInterviewConfig({ ...interviewConfig, difficulty: event.target.value })}><option>Beginner</option><option>Intermediate</option><option>Advanced</option></select></label>
                <label>Questions<input type="number" min="1" max="20" value={interviewConfig.question_count} onChange={(event) => setInterviewConfig({ ...interviewConfig, question_count: Number(event.target.value) })} /></label>
                <label>Minutes<input type="number" min="5" max="180" value={interviewConfig.duration_minutes} onChange={(event) => setInterviewConfig({ ...interviewConfig, duration_minutes: Number(event.target.value) })} /></label>
              </div>
              <button className="primary-button" disabled={!resumeAnalysis || (Boolean(job) && !match) || busy === "interview-start"} onClick={startInterview}>
                {busy === "interview-start" ? "Preparing..." : "Start interview"} <span>→</span>
              </button>
            </>
          ) : (
            <InterviewView interview={interview} answer={answer} setAnswer={setAnswer} submitAnswer={submitAnswer} completeInterview={completeInterview} busy={busy} />
          )}
        </section>
        </>}
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

function InterviewView({ interview, answer, setAnswer, submitAnswer, completeInterview, busy }) {
  const answered = interview.questions.filter((item) => item.status === "answered");
  const current = interview.question;
  const latestEvaluation = answered.length ? answered[answered.length - 1].evaluation : null;
  return <div className="interview-view">
    <div className="progress-row"><span>Question {Math.min(interview.current_question_index + 1, interview.question_count)} of {interview.question_count}</span><span>{interview.status}</span></div>
    {current ? <div className="question-card"><p className="eyebrow">{current.question_type}</p><h4>{current.question}</h4>
      <textarea className="job-input answer-input" value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Write your answer here..." disabled={current.status === "answered" || interview.status !== "active"} />
      <button className="primary-button" disabled={!answer.trim() || busy === "interview-answer" || interview.status !== "active"} onClick={submitAnswer}>{busy === "interview-answer" ? "Evaluating..." : "Submit answer"} <span>→</span></button>
    </div> : <p className="muted">All configured questions have been answered.</p>}
    {latestEvaluation && <div className="evaluation-card"><strong>Latest evaluation · {latestEvaluation.score}/100</strong><p>{latestEvaluation.feedback}</p><TagList title="Strengths" items={latestEvaluation.strengths} /><TagList title="Improvement areas" items={latestEvaluation.weaknesses} /></div>}
    {interview.status !== "completed" && <button className="secondary-button end-interview" disabled={busy === "interview-complete"} onClick={completeInterview}>{busy === "interview-complete" ? "Completing..." : "End interview"}</button>}
    {interview.summary && <div className="evaluation-card"><strong>Interview summary · {interview.summary.overall_score}/100</strong><p>{interview.summary.summary}</p><TagList title="Strengths" items={interview.summary.strengths} /><TagList title="Improvement areas" items={interview.summary.improvement_areas} /></div>}
  </div>;
}

function DashboardView({ dashboard, reports, onOpenReport }) {
  if (!dashboard) return <section className="panel empty-state"><h2>Dashboard unavailable</h2><p className="muted">The dashboard summary could not be loaded yet.</p></section>;
  if (!dashboard.total_interviews_completed) return <section className="panel empty-state"><p className="eyebrow cyan">Progress dashboard</p><h2>No completed interviews yet</h2><p className="muted">Complete your first mock interview to see verified scores, skill trends, and recommendations here.</p></section>;
  return <div className="report-layout">
    <div className="section-heading"><div><p className="eyebrow cyan">Progress dashboard</p><h2>Your preparation signals</h2></div></div>
    <div className="metrics-grid report-metrics">
      <Metric label="Completed interviews" value={dashboard.total_interviews_completed} />
      <Metric label="Average score" value={`${dashboard.average_interview_score}/100`} />
      <Metric label="Recorded matches" value={dashboard.matching_overview.total_matches} />
    </div>
    <section className="panel report-section"><div className="panel-heading"><h3>Performance trend</h3></div>{dashboard.performance_trend.map((item) => <div className="trend-row" key={item.date}><span>{new Date(item.date).toLocaleDateString()}</span><strong>{item.score}/100</strong><div className="bar"><span style={{ width: `${item.score}%` }} /></div></div>)}</section>
    <section className="panel report-section"><div className="panel-heading"><h3>Skill performance</h3></div><SkillBars skills={dashboard.skill_performance} /></section>
    <section className="panel report-section"><div className="panel-heading"><h3>Recent interview history</h3></div>{(reports.length ? reports : dashboard.recent_interviews).map((item) => <button className="history-row" key={item.id} onClick={() => onOpenReport(item.id)}><span>#{item.interview_id} · {item.interview_type}</span><strong>{item.overall_score}/100</strong><span>{new Date(item.created_at).toLocaleDateString()}</span></button>)}</section>
    <section className="panel report-section"><div className="panel-heading"><h3>Areas for improvement</h3></div><TagList title="From recorded evaluations" items={dashboard.areas_for_improvement} /></section>
  </div>;
}

function ReportView({ report, apiBaseUrl }) {
  if (!report) return <section className="panel empty-state"><h2>Select a completed interview</h2><p className="muted">Completed interview reports will appear in History.</p></section>;
  return <div className="report-layout">
    <div className="section-heading"><div><p className="eyebrow cyan">Interview report · {report.interview_type}</p><h2>Performance assessment</h2></div><a className="secondary-button report-download" href={`${apiBaseUrl}/api/v1/reports/${report.id}/pdf`}>Download PDF <span>↓</span></a></div>
    <section className="panel report-hero"><div className="report-score"><strong>{report.overall_score}</strong><span>/100</span></div><div><h3>{report.final_assessment.readiness_assessment}</h3><p className="muted">{report.disclaimer}</p><p className="muted">{report.answered_questions} of {report.total_questions} questions answered · {report.duration_minutes} configured minutes</p></div></section>
    <section className="panel report-section"><div className="panel-heading"><h3>Skill-wise performance</h3></div><SkillBars skills={report.skill_performance} /></section>
    <section className="panel report-section"><div className="panel-heading"><h3>Question-level feedback</h3></div>{report.question_feedback.map((item) => <article className="question-report" key={item.sequence}><p className="eyebrow">Question {item.sequence} · {item.question_type}</p><h4>{item.question}</h4><p><strong>Answer:</strong> {item.answer || "Not answered"}</p>{item.evaluation_score !== null && <p><strong>Score:</strong> {item.evaluation_score}/100</p>}<p>{item.feedback}</p><TagList title="Strengths" items={item.strengths} /><TagList title="Weaknesses" items={item.weaknesses} /><TagList title="Suggested improved answer" items={item.suggested_improved_answer ? [item.suggested_improved_answer] : []} /></article>)}</section>
    <section className="panel report-section"><div className="panel-heading"><h3>Recommendations</h3></div><TagList title="Preparation topics" items={report.recommended_preparation_topics} /><TagList title="Next steps" items={report.personalized_next_steps} /><TagList title="Missing concepts" items={report.missing_technical_concepts} /></section>
    <section className="panel report-section"><div className="panel-heading"><h3>Final assessment</h3></div><TagList title="Overall strengths" items={report.final_assessment.overall_strengths} /><TagList title="Areas requiring practice" items={report.final_assessment.areas_requiring_practice} /><p className="muted">{report.final_assessment.summary}</p></section>
  </div>;
}

function Metric({ label, value }) { return <div className="metric-card"><p>{label}</p><strong>{value}</strong></div>; }

function SkillBars({ skills }) {
  if (!skills) return <p className="muted">No completed interview data yet.</p>;
  return <div>{Object.entries(skills).map(([name, value]) => <div className="skill-row" key={name}><div><span>{name.replaceAll("_", " ")}</span><strong>{value}/100</strong></div><div className="bar"><span style={{ width: `${value}%` }} /></div></div>)}</div>;
}

export default App;
