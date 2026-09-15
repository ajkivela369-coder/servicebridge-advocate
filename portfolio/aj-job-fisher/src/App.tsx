import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  ClipboardList,
  Clock3,
  Download,
  FileText,
  Filter,
  Inbox,
  Link2,
  LogIn,
  LogOut,
  Mail,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  WandSparkles,
  X,
} from 'lucide-react';
import { api, auth } from '@appdeploy/client';

type ScoreComponents = {
  hardQualifications: number;
  backgroundMatch: number;
  flexibilityFit: number;
  compensationFit: number;
  domainRelevance: number;
  applicationFriction: number;
  strategicValue: number;
};

type Job = {
  id: string;
  company: string;
  title: string;
  location: string;
  employmentType: string;
  compensation: string;
  source: string;
  sourceUrl: string;
  directUrl: string;
  remoteEligible: boolean;
  requiredCredentialsVerified: boolean;
  travelPercent: number;
  score: number;
  scoreComponents: ScoreComponents;
  stopConditions: string[];
  concerns: string;
  notes: string;
  disposition: string;
  firstSeen: string;
  lastVerified: string;
  appliedAt: string;
  confirmationNumber: string;
  resumeVersion: string;
  followUpDate: string;
  atsKeywords?: string[];
  summary?: string;
  schedule?: string;
  remoteEvidence?: string;
  requiredCredentials?: string[];
  preferredCredentials?: string[];
  applicationRisks?: string[];
  payFloorStatus?: string;
  applicationPackage?: string;
  packageGeneratedAt?: string;
};

type Scan = {
  id: string;
  createdAt: string;
  source: string;
  url: string;
  reviewed: number;
  newLive: number;
  strong: number;
  blocked: number;
  duplicates: number;
  label: string;
};

type RecruiterMessage = {
  id: string;
  sender: string;
  company: string;
  role: string;
  subject: string;
  receivedAt: string;
  type: string;
  actionNeeded: string;
  deadline: string;
  summary: string;
  suggestedReply: string;
  rawPreview: string;
};

type FormState = {
  company: string;
  title: string;
  location: string;
  employmentType: string;
  compensation: string;
  source: string;
  sourceUrl: string;
  directUrl: string;
  remoteEligible: boolean;
  requiredCredentialsVerified: boolean;
  travelPercent: number;
  scoreComponents: ScoreComponents;
  stopConditions: string[];
  concerns: string;
  notes: string;
  disposition: string;
};

type Tab = 'pipeline' | 'queue' | 'analytics' | 'inbox';

const STOP_OPTIONS = [
  'Medical/disability question',
  'Background-check authorization',
  'Driving/vehicle requirement',
  'Binding agreement',
  'Reference request',
  'Start-date commitment',
  'Drug test or medical exam',
  'Unusual free-response question',
];

const DISPOSITIONS: Record<string, string> = {
  ready: 'Ready to auto-apply',
  blocked: 'Needs review',
  package_ready: 'One-click package',
  near_match: 'Near match',
  submitted: 'Submitted',
  interview: 'Interview',
  rejected: 'Rejected',
};

const blankForm = (): FormState => ({
  company: '',
  title: '',
  location: 'Remote — U.S.',
  employmentType: 'Full-time',
  compensation: '',
  source: '',
  sourceUrl: '',
  directUrl: '',
  remoteEligible: true,
  requiredCredentialsVerified: true,
  travelPercent: 0,
  scoreComponents: {
    hardQualifications: 20,
    backgroundMatch: 16,
    flexibilityFit: 15,
    compensationFit: 12,
    domainRelevance: 8,
    applicationFriction: 8,
    strategicValue: 4,
  },
  stopConditions: [],
  concerns: '',
  notes: '',
  disposition: '',
});

const scoreLabels: Array<[keyof ScoreComponents, string, number]> = [
  ['hardQualifications', 'Hard qualifications', 25],
  ['backgroundMatch', 'Background match', 20],
  ['flexibilityFit', 'Remote / flexibility', 15],
  ['compensationFit', 'Compensation', 15],
  ['domainRelevance', 'Domain relevance', 10],
  ['applicationFriction', 'Application friction', 10],
  ['strategicValue', 'Strategic value', 5],
];

function formatDate(value: string) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function App() {
  const [user, setUser] = useState<{ name?: string; email?: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [inboxMessages, setInboxMessages] = useState<RecruiterMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [tab, setTab] = useState<Tab>('pipeline');
  const [showForm, setShowForm] = useState(false);
  const [showIngest, setShowIngest] = useState(false);
  const [form, setForm] = useState<FormState>(blankForm());
  const [selected, setSelected] = useState<Job | null>(null);
  const [saving, setSaving] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [packageBusy, setPackageBusy] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setErrorMessage('');
    try {
      const { data } = await api.get('/api/dashboard');
      setJobs((data.jobs ?? []) as Job[]);
      setScans((data.scans ?? []) as Scan[]);
      setInboxMessages((data.inbox ?? []) as RecruiterMessage[]);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not load Job Fisher.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      try {
        const current = await auth.getUser();
        if (current) {
          setUser({ name: current.name, email: current.email });
          await loadDashboard();
        }
      } finally {
        setAuthLoading(false);
      }
    })();
  }, []);

  const metrics = useMemo(
    () => ({
      total: jobs.length,
      strong: jobs.filter(job => job.score >= 85).length,
      submitted: jobs.filter(job => ['submitted', 'interview'].includes(job.disposition)).length,
      blocked: jobs.filter(job => job.disposition === 'blocked').length,
    }),
    [jobs]
  );

  const filteredJobs = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return jobs
      .filter(job => filter === 'all' || job.disposition === filter)
      .filter(job =>
        !needle ||
        `${job.company} ${job.title} ${job.source}`.toLowerCase().includes(needle)
      )
      .sort((a, b) => b.score - a.score);
  }, [jobs, query, filter]);

  const queueJobs = useMemo(
    () =>
      jobs
        .filter(job => job.score >= 75 && job.disposition !== 'rejected')
        .sort((a, b) => {
          const blockedDelta = Number(Boolean(a.stopConditions?.length)) - Number(Boolean(b.stopConditions?.length));
          return blockedDelta || b.score - a.score;
        }),
    [jobs]
  );

  async function signIn() {
    setErrorMessage('');
    try {
      const result = await auth.signIn();
      setUser({ name: result.user.name, email: result.user.email });
      await loadDashboard();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Sign-in did not complete.');
    }
  }

  async function signOut() {
    await auth.signOut();
    setUser(null);
    setJobs([]);
    setScans([]);
    setInboxMessages([]);
    setSelected(null);
  }

  async function createJob(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setErrorMessage('');
    try {
      const { data } = await api.post('/api/jobs', form);
      const created = data.job as Job;
      setJobs(current => [created, ...current]);
      setForm(blankForm());
      setShowForm(false);
      setSelected(created);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not add this candidate.');
    } finally {
      setSaving(false);
    }
  }

  async function ingestUrl(url: string) {
    setIngesting(true);
    setErrorMessage('');
    try {
      const { data } = await api.post('/api/ingest', { url });
      const created = data.job as Job;
      setJobs(current => [created, ...current]);
      if (data.scan) setScans(current => [data.scan as Scan, ...current]);
      setShowIngest(false);
      setSelected(created);
      setTab('pipeline');
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not analyze that job URL.');
    } finally {
      setIngesting(false);
    }
  }

  async function updateJob(job: Job, patch: Record<string, unknown>) {
    setErrorMessage('');
    try {
      const { data } = await api.put(`/api/jobs/${job.id}`, patch);
      const updated = data.job as Job;
      setJobs(current => current.map(item => (item.id === updated.id ? updated : item)));
      if (selected?.id === updated.id) setSelected(updated);
      return updated;
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not update the candidate.');
      return null;
    }
  }

  async function generatePackage(job: Job) {
    setPackageBusy(true);
    setErrorMessage('');
    try {
      const { data } = await api.post(`/api/jobs/${job.id}/package`, {});
      const updated = data.job as Job;
      setJobs(current => current.map(item => (item.id === updated.id ? updated : item)));
      setSelected(updated);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not generate the application package.');
    } finally {
      setPackageBusy(false);
    }
  }

  async function deleteJob(job: Job) {
    if (!window.confirm(`Delete ${job.company} — ${job.title}?`)) return;
    setErrorMessage('');
    try {
      await api.delete(`/api/jobs/${job.id}`);
      setJobs(current => current.filter(item => item.id !== job.id));
      if (selected?.id === job.id) setSelected(null);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not delete the candidate.');
    }
  }

  async function parseRecruiter(text: string) {
    setSaving(true);
    setErrorMessage('');
    try {
      const { data } = await api.post('/api/inbox/parse', { text });
      setInboxMessages(current => [data.message as RecruiterMessage, ...current]);
      return true;
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not analyze the recruiter message.');
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function dismissRecruiter(message: RecruiterMessage) {
    try {
      await api.delete(`/api/inbox/${message.id}`);
      setInboxMessages(current => current.filter(item => item.id !== message.id));
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not dismiss the recruiter message.');
    }
  }

  if (authLoading) {
    return (
      <main className="center-screen">
        <div className="pulse-mark"><Sparkles size={24} /></div>
        <p>Loading Job Fisher…</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="brand-mark"><BriefcaseBusiness size={26} /></div>
          <span className="eyebrow">PRIVATE JOB OPERATIONS</span>
          <h1>AJ Job Fisher</h1>
          <p className="login-copy">
            A persistent control center for high-fit remote roles, ATS analysis, application guardrails,
            tailored packages, recruiter responses, and follow-up tracking.
          </p>
          <div className="rule-grid">
            <div><ShieldCheck size={18} /><span>85+ auto-apply threshold</span></div>
            <div><CircleDollarSign size={18} /><span>$20/hr or $40k floor</span></div>
            <div><AlertTriangle size={18} /><span>Mandatory stop conditions</span></div>
          </div>
          <button className="primary wide" onClick={() => void signIn()}>
            <LogIn size={18} /> Sign in to Job Fisher
          </button>
          {errorMessage && <p className="error-banner">{errorMessage}</p>}
        </section>
      </main>
    );
  }

  const tabMeta: Record<Tab, { eyebrow: string; title: string; copy: string }> = {
    pipeline: {
      eyebrow: 'AUTONOMOUS SEARCH LEDGER',
      title: 'Job pipeline',
      copy: 'Import live jobs, rank opportunities, stop risky submissions, and preserve evidence.',
    },
    queue: {
      eyebrow: 'APPLICATION OPERATIONS',
      title: 'Application queue',
      copy: 'Work highest-fit roles first and keep stop-condition jobs out of autonomous submission.',
    },
    analytics: {
      eyebrow: 'SEARCH INTELLIGENCE',
      title: 'Scan analytics',
      copy: 'See what Job Fisher has reviewed, how many strong matches surfaced, and where blockers cluster.',
    },
    inbox: {
      eyebrow: 'HIRING RESPONSES',
      title: 'Recruiter inbox',
      copy: 'Paste hiring messages for structured triage and a cautious suggested reply.',
    },
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark small"><BriefcaseBusiness size={20} /></div>
          <div><strong>Job Fisher</strong><span>Control Center</span></div>
        </div>
        <nav>
          <button className={tab === 'pipeline' ? 'nav-active' : ''} onClick={() => setTab('pipeline')}>
            <Sparkles size={17} /> Candidate ledger
          </button>
          <button className={tab === 'queue' ? 'nav-active' : ''} onClick={() => setTab('queue')}>
            <ClipboardList size={17} /> Application queue
          </button>
          <button className={tab === 'analytics' ? 'nav-active' : ''} onClick={() => setTab('analytics')}>
            <BarChart3 size={17} /> Scan analytics
          </button>
          <button className={tab === 'inbox' ? 'nav-active' : ''} onClick={() => setTab('inbox')}>
            <Inbox size={17} /> Recruiter inbox
          </button>
        </nav>
        <div className="policy-card">
          <span className="eyebrow">STANDING POLICY</span>
          <p><b>Remote U.S.</b> only</p>
          <p><b>Travel</b> ≤ 10%</p>
          <p><b>Floor</b> $20/hr · $40k/yr</p>
          <p><b>Auto-submit</b> 85+ with no stops</p>
        </div>
        <div className="user-card">
          <div><strong>{user.name || 'AJ'}</strong><span>{user.email || 'Signed in'}</span></div>
          <button onClick={() => void signOut()} title="Sign out"><LogOut size={17} /></button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="eyebrow">{tabMeta[tab].eyebrow}</span>
            <h1>{tabMeta[tab].title}</h1>
            <p>{tabMeta[tab].copy}</p>
          </div>
          {tab === 'pipeline' && (
            <div className="topbar-actions">
              <button className="secondary" onClick={() => setShowIngest(true)}><Link2 size={18} /> Analyze URL</button>
              <button className="primary" onClick={() => setShowForm(true)}><Plus size={18} /> Add candidate</button>
            </div>
          )}
        </header>

        {errorMessage && (
          <div className="error-banner">
            <AlertTriangle size={17} /> {errorMessage}
            <button onClick={() => setErrorMessage('')}><X size={16} /></button>
          </div>
        )}

        <section className="metrics-grid">
          <Metric label="Tracked" value={metrics.total} icon={<BriefcaseBusiness size={19} />} />
          <Metric label="85+ matches" value={metrics.strong} icon={<Sparkles size={19} />} />
          <Metric label="Submitted / interview" value={metrics.submitted} icon={<CheckCircle2 size={19} />} />
          <Metric label="Needs review" value={metrics.blocked} icon={<AlertTriangle size={19} />} />
        </section>

        {tab === 'pipeline' && (
          <PipelineView
            jobs={filteredJobs}
            loading={loading}
            query={query}
            filter={filter}
            onQuery={setQuery}
            onFilter={setFilter}
            onOpen={setSelected}
          />
        )}
        {tab === 'queue' && (
          <QueueView jobs={queueJobs} onOpen={setSelected} onUpdate={updateJob} />
        )}
        {tab === 'analytics' && <AnalyticsView scans={scans} jobs={jobs} />}
        {tab === 'inbox' && (
          <RecruiterInbox
            messages={inboxMessages}
            saving={saving}
            onParse={parseRecruiter}
            onDismiss={dismissRecruiter}
          />
        )}
      </main>

      {showForm && (
        <CandidateForm
          form={form}
          setForm={setForm}
          onClose={() => setShowForm(false)}
          onSubmit={createJob}
          saving={saving}
        />
      )}
      {showIngest && (
        <UrlIngestModal
          busy={ingesting}
          onClose={() => setShowIngest(false)}
          onSubmit={ingestUrl}
        />
      )}
      {selected && (
        <DetailPanel
          job={selected}
          packageBusy={packageBusy}
          onClose={() => setSelected(null)}
          onUpdate={updateJob}
          onGeneratePackage={generatePackage}
          onDelete={deleteJob}
        />
      )}
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="metric-card">
      <div className="metric-icon">{icon}</div>
      <div><strong>{value}</strong><span>{label}</span></div>
    </div>
  );
}

function Score({ score }: { score: number }) {
  const tone = score >= 85 ? 'score-high' : score >= 75 ? 'score-mid' : 'score-low';
  return <div className={`score-pill ${tone}`}><strong>{score}</strong><span>/100</span></div>;
}

function Status({ disposition }: { disposition: string }) {
  return <span className={`status status-${disposition}`}>{DISPOSITIONS[disposition] || disposition}</span>;
}

function PipelineView({
  jobs,
  loading,
  query,
  filter,
  onQuery,
  onFilter,
  onOpen,
}: {
  jobs: Job[];
  loading: boolean;
  query: string;
  filter: string;
  onQuery: (value: string) => void;
  onFilter: (value: string) => void;
  onOpen: (job: Job) => void;
}) {
  return (
    <>
      <section className="toolbar">
        <label className="search-box"><Search size={17} /><input value={query} onChange={event => onQuery(event.target.value)} placeholder="Search company, role, source…" /></label>
        <label className="filter-box">
          <Filter size={16} />
          <select value={filter} onChange={event => onFilter(event.target.value)}>
            <option value="all">All dispositions</option>
            {Object.entries(DISPOSITIONS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
          </select>
        </label>
      </section>
      <section className="ledger">
        <div className="ledger-head"><span>Opportunity</span><span>Fit</span><span>Disposition</span><span>Verified</span><span></span></div>
        {loading ? (
          <div className="empty-state">Refreshing ledger…</div>
        ) : jobs.length === 0 ? (
          <div className="empty-state"><BriefcaseBusiness size={30} /><h3>No candidates here yet</h3><p>Analyze a live job URL or add a candidate manually.</p></div>
        ) : (
          jobs.map(job => (
            <article className="job-row" key={job.id} onClick={() => onOpen(job)}>
              <div className="job-primary">
                <strong>{job.title}</strong>
                <span>{job.company} · {job.location}</span>
                <small>{job.compensation || 'Compensation not listed'} · {job.source || 'Direct'}</small>
              </div>
              <Score score={job.score} />
              <Status disposition={job.disposition} />
              <div className="verified-cell">
                <span>{formatDate(job.lastVerified)}</span>
                {Boolean(job.stopConditions?.length) && <small><AlertTriangle size={13} /> {job.stopConditions.length} stop{job.stopConditions.length === 1 ? '' : 's'}</small>}
              </div>
              <ChevronRight className="chevron" size={18} />
            </article>
          ))
        )}
      </section>
    </>
  );
}

function QueueView({
  jobs,
  onOpen,
  onUpdate,
}: {
  jobs: Job[];
  onOpen: (job: Job) => void;
  onUpdate: (job: Job, patch: Record<string, unknown>) => Promise<Job | null>;
}) {
  if (!jobs.length) {
    return <div className="empty-state standalone"><ClipboardList size={30} /><h3>Queue is clear</h3><p>75+ opportunities will appear here.</p></div>;
  }
  return (
    <section className="queue-grid">
      {jobs.map(job => {
        const blocked = Boolean(job.stopConditions?.length);
        return (
          <article className="queue-card" key={job.id}>
            <div className="queue-card-head">
              <div><span className="eyebrow">{blocked ? 'HOLD' : job.score >= 85 ? 'AUTO-APPLY LANE' : 'PACKAGE LANE'}</span><h3>{job.title}</h3><p>{job.company}</p></div>
              <Score score={job.score} />
            </div>
            <Status disposition={job.disposition} />
            {blocked ? (
              <div className="queue-stops">{job.stopConditions.map(stop => <span key={stop}><AlertTriangle size={13} /> {stop}</span>)}</div>
            ) : (
              <div className="queue-clear"><CheckCircle2 size={15} /> No mandatory stops recorded</div>
            )}
            <div className="queue-actions">
              <button className="secondary" onClick={() => onOpen(job)}>Open</button>
              {!blocked && job.disposition !== 'submitted' && job.disposition !== 'interview' && (
                <button className="primary" onClick={() => void onUpdate(job, { disposition: 'submitted', appliedAt: new Date().toISOString() })}>
                  Mark submitted
                </button>
              )}
            </div>
          </article>
        );
      })}
    </section>
  );
}

function AnalyticsView({ scans, jobs }: { scans: Scan[]; jobs: Job[] }) {
  const ordered = [...scans].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()).slice(-12);
  const reviewed = scans.reduce((sum, scan) => sum + (scan.reviewed || 0), 0);
  const strong = scans.reduce((sum, scan) => sum + (scan.strong || 0), 0);
  const blocked = scans.reduce((sum, scan) => sum + (scan.blocked || 0), 0);
  const maxValue = Math.max(1, ...ordered.map(scan => Math.max(scan.reviewed || 0, scan.strong || 0, scan.blocked || 0)));
  return (
    <div className="analytics-layout">
      <section className="analytics-summary">
        <div><strong>{reviewed}</strong><span>URL analyses</span></div>
        <div><strong>{strong}</strong><span>85+ from URL scans</span></div>
        <div><strong>{blocked}</strong><span>Blocked by policy</span></div>
        <div><strong>{jobs.filter(job => job.applicationPackage).length}</strong><span>Packages generated</span></div>
      </section>
      <section className="chart-card">
        <div className="section-title"><div><h3>Recent URL analyses</h3><p>Reviewed · strong · blocked</p></div></div>
        {ordered.length ? (
          <div className="scan-chart">
            {ordered.map(scan => (
              <div className="scan-column" key={scan.id} title={scan.label}>
                <div className="bars">
                  <i className="bar-reviewed" style={{ height: `${Math.max(8, (scan.reviewed / maxValue) * 100)}%` }}></i>
                  <i className="bar-strong" style={{ height: `${scan.strong ? Math.max(8, (scan.strong / maxValue) * 100) : 2}%` }}></i>
                  <i className="bar-blocked" style={{ height: `${scan.blocked ? Math.max(8, (scan.blocked / maxValue) * 100) : 2}%` }}></i>
                </div>
                <span>{formatDate(scan.createdAt).replace(/, \d{4}/, '')}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state"><BarChart3 size={28} /><h3>No scan history yet</h3><p>Use Analyze URL in the pipeline to create the first scan event.</p></div>
        )}
      </section>
      <section className="chart-card">
        <div className="section-title"><div><h3>Pipeline funnel</h3><p>Current persistent ledger</p></div></div>
        <div className="funnel-list">
          <FunnelRow label="Tracked" value={jobs.length} max={Math.max(1, jobs.length)} />
          <FunnelRow label="75+" value={jobs.filter(job => job.score >= 75).length} max={Math.max(1, jobs.length)} />
          <FunnelRow label="85+" value={jobs.filter(job => job.score >= 85).length} max={Math.max(1, jobs.length)} />
          <FunnelRow label="Submitted" value={jobs.filter(job => ['submitted', 'interview'].includes(job.disposition)).length} max={Math.max(1, jobs.length)} />
          <FunnelRow label="Interview" value={jobs.filter(job => job.disposition === 'interview').length} max={Math.max(1, jobs.length)} />
        </div>
      </section>
    </div>
  );
}

function FunnelRow({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div className="funnel-row"><span>{label}</span><div><i style={{ width: `${(value / max) * 100}%` }}></i></div><b>{value}</b></div>
  );
}

function RecruiterInbox({
  messages,
  saving,
  onParse,
  onDismiss,
}: {
  messages: RecruiterMessage[];
  saving: boolean;
  onParse: (text: string) => Promise<boolean>;
  onDismiss: (message: RecruiterMessage) => Promise<void>;
}) {
  const [text, setText] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (await onParse(text)) setText('');
  }
  return (
    <div className="inbox-layout">
      <form className="message-parser" onSubmit={submit}>
        <div className="section-title"><div><h3>Paste recruiter or hiring email</h3><p>Job Fisher extracts the action, deadline, and a cautious suggested reply.</p></div><WandSparkles size={20} /></div>
        <textarea value={text} onChange={event => setText(event.target.value)} rows={8} placeholder="Paste the email or hiring message here…" />
        <button className="primary" disabled={saving || text.trim().length < 20}>{saving ? 'Analyzing…' : 'Analyze & save'}</button>
      </form>
      <section className="message-list">
        {!messages.length ? (
          <div className="empty-state standalone"><Mail size={30} /><h3>No recruiter messages saved</h3><p>Paste a recruiter email above to start the response queue.</p></div>
        ) : (
          [...messages].sort((a, b) => new Date(b.receivedAt).getTime() - new Date(a.receivedAt).getTime()).map(message => (
            <article className="message-card" key={message.id}>
              <div className="message-card-head"><div><span className="eyebrow">{message.type}</span><h3>{message.subject || message.role || 'Hiring message'}</h3><p>{message.sender}{message.company ? ` · ${message.company}` : ''}</p></div><button className="icon-button" onClick={() => void onDismiss(message)} title="Dismiss"><X size={17} /></button></div>
              <p>{message.summary}</p>
              {message.actionNeeded && <div className="action-needed"><Clock3 size={15} /><span><b>Next:</b> {message.actionNeeded}{message.deadline ? ` · ${message.deadline}` : ''}</span></div>}
              <div className="reply-box"><strong>Suggested reply</strong><pre>{message.suggestedReply}</pre><button className="secondary" onClick={() => void navigator.clipboard.writeText(message.suggestedReply)}>Copy reply</button></div>
            </article>
          ))
        )}
      </section>
    </div>
  );
}

function UrlIngestModal({ busy, onClose, onSubmit }: { busy: boolean; onClose: () => void; onSubmit: (url: string) => Promise<void> }) {
  const [url, setUrl] = useState('');
  return (
    <div className="modal-backdrop" role="presentation">
      <form className="url-modal" onSubmit={event => { event.preventDefault(); void onSubmit(url); }}>
        <div className="panel-head"><div><span className="eyebrow">ATS URL INGESTION</span><h2>Analyze a live job URL</h2><p>Scrape the posting, extract ATS requirements, score it, detect stop conditions, and add it to the ledger.</p></div><button type="button" className="icon-button" onClick={onClose}><X size={19} /></button></div>
        <label className="full-label">Job URL<input className="text-input" type="url" required value={url} onChange={event => setUrl(event.target.value)} placeholder="https://company.com/careers/…" /></label>
        <div className="ingest-note"><ShieldCheck size={17} /><span>Job Fisher does not invent credentials. Unclear remote eligibility or hard requirements are treated conservatively.</span></div>
        <div className="form-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Reading & scoring…' : 'Analyze job'}</button></div>
      </form>
    </div>
  );
}

function CandidateForm({ form, setForm, onClose, onSubmit, saving }: { form: FormState; setForm: React.Dispatch<React.SetStateAction<FormState>>; onClose: () => void; onSubmit: (event: FormEvent) => void; saving: boolean }) {
  const projectedScore = Object.values(form.scoreComponents).reduce((sum, value) => sum + value, 0);
  function toggleStop(option: string) {
    setForm(current => ({
      ...current,
      stopConditions: current.stopConditions.includes(option)
        ? current.stopConditions.filter(item => item !== option)
        : [...current.stopConditions, option],
    }));
  }
  return (
    <div className="modal-backdrop" role="presentation">
      <form className="candidate-form" onSubmit={onSubmit}>
        <div className="panel-head"><div><span className="eyebrow">NEW OPPORTUNITY</span><h2>Add candidate</h2></div><button type="button" className="icon-button" onClick={onClose}><X size={19} /></button></div>
        <div className="form-grid">
          <label>Company<input required value={form.company} onChange={event => setForm({ ...form, company: event.target.value })} /></label>
          <label>Role<input required value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} /></label>
          <label>Location<input value={form.location} onChange={event => setForm({ ...form, location: event.target.value })} /></label>
          <label>Compensation<input value={form.compensation} onChange={event => setForm({ ...form, compensation: event.target.value })} placeholder="$25/hr or $55k–$70k" /></label>
          <label>Source<input value={form.source} onChange={event => setForm({ ...form, source: event.target.value })} placeholder="Employer, LinkedIn, USAJOBS…" /></label>
          <label>Employment type<select value={form.employmentType} onChange={event => setForm({ ...form, employmentType: event.target.value })}><option>Full-time</option><option>Part-time</option><option>Contract</option><option>Temporary</option></select></label>
          <label className="span-2">Direct application URL<input type="url" value={form.directUrl} onChange={event => setForm({ ...form, directUrl: event.target.value })} placeholder="https://…" /></label>
          <label>Travel %<input type="number" min="0" max="100" value={form.travelPercent} onChange={event => setForm({ ...form, travelPercent: Number(event.target.value) })} /></label>
          <label className="toggle-label"><input type="checkbox" checked={form.remoteEligible} onChange={event => setForm({ ...form, remoteEligible: event.target.checked })} /> Remote eligible for AJ</label>
          <label className="toggle-label"><input type="checkbox" checked={form.requiredCredentialsVerified} onChange={event => setForm({ ...form, requiredCredentialsVerified: event.target.checked })} /> Required credentials verified</label>
        </div>
        <div className="score-builder">
          <div className="section-title"><div><h3>Fit score</h3><p>Weighted 0–100 model</p></div><Score score={projectedScore} /></div>
          {scoreLabels.map(([key, label, max]) => (
            <label className="slider-row" key={key}><span>{label}<b>{form.scoreComponents[key]}/{max}</b></span><input type="range" min="0" max={max} value={form.scoreComponents[key]} onChange={event => setForm({ ...form, scoreComponents: { ...form.scoreComponents, [key]: Number(event.target.value) } })} /></label>
          ))}
        </div>
        <div className="stops-builder">
          <div className="section-title"><div><h3>Mandatory stops</h3><p>Any checked item blocks autonomous submission.</p></div></div>
          <div className="stop-grid">{STOP_OPTIONS.map(option => <label key={option} className={form.stopConditions.includes(option) ? 'stop-option checked' : 'stop-option'}><input type="checkbox" checked={form.stopConditions.includes(option)} onChange={() => toggleStop(option)} />{option}</label>)}</div>
        </div>
        <label className="full-label">Concerns<textarea rows={2} value={form.concerns} onChange={event => setForm({ ...form, concerns: event.target.value })} placeholder="Shift requirements, phone volume, hidden travel…" /></label>
        <label className="full-label">Notes<textarea rows={2} value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} /></label>
        <div className="form-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={saving}>{saving ? 'Saving…' : 'Add to ledger'}</button></div>
      </form>
    </div>
  );
}

function DetailPanel({
  job,
  packageBusy,
  onClose,
  onUpdate,
  onGeneratePackage,
  onDelete,
}: {
  job: Job;
  packageBusy: boolean;
  onClose: () => void;
  onUpdate: (job: Job, patch: Record<string, unknown>) => Promise<Job | null>;
  onGeneratePackage: (job: Job) => Promise<void>;
  onDelete: (job: Job) => Promise<void>;
}) {
  const [confirmation, setConfirmation] = useState(job.confirmationNumber || '');
  const [resumeVersion, setResumeVersion] = useState(job.resumeVersion || '');
  const [followUpDate, setFollowUpDate] = useState(job.followUpDate || '');

  useEffect(() => {
    setConfirmation(job.confirmationNumber || '');
    setResumeVersion(job.resumeVersion || '');
    setFollowUpDate(job.followUpDate || '');
  }, [job.id, job.confirmationNumber, job.resumeVersion, job.followUpDate]);

  function downloadPackage() {
    if (!job.applicationPackage) return;
    const blob = new Blob([job.applicationPackage], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${job.company}-${job.title}-application-package.md`.replace(/[^a-z0-9._-]+/gi, '-');
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="detail-panel">
      <div className="panel-head"><div><span className="eyebrow">CANDIDATE DETAIL</span><h2>{job.title}</h2><p>{job.company}</p></div><button className="icon-button" onClick={onClose}><X size={19} /></button></div>
      <div className="detail-score"><Score score={job.score} /><div><Status disposition={job.disposition} /><p>First seen {formatDate(job.firstSeen)}</p></div></div>
      <section className="detail-section">
        <h3>Decision</h3>
        <label>Disposition<select value={job.disposition} onChange={event => void onUpdate(job, { disposition: event.target.value })}>{Object.entries(DISPOSITIONS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      </section>
      <section className="detail-section">
        <h3>Policy checks</h3>
        <div className="check-line"><ShieldCheck size={17} /><span>{job.remoteEligible ? 'Remote eligibility confirmed' : 'Remote eligibility failed or unclear'}</span></div>
        <div className="check-line"><ShieldCheck size={17} /><span>{job.requiredCredentialsVerified ? 'Required credentials appear compatible' : 'Required credentials need review'}</span></div>
        <div className="check-line"><Clock3 size={17} /><span>{job.travelPercent}% travel recorded</span></div>
        {job.stopConditions?.length ? <div className="stop-list">{job.stopConditions.map(stop => <span key={stop}><AlertTriangle size={14} />{stop}</span>)}</div> : <div className="clear-stop"><CheckCircle2 size={16} />No mandatory stop conditions</div>}
      </section>
      {(job.summary || job.atsKeywords?.length || job.requiredCredentials?.length) && (
        <section className="detail-section">
          <h3>ATS analysis</h3>
          {job.summary && <p>{job.summary}</p>}
          {job.atsKeywords?.length ? <div className="keyword-cloud">{job.atsKeywords.map(keyword => <span key={keyword}>{keyword}</span>)}</div> : null}
          {job.requiredCredentials?.length ? <p><b>Required:</b> {job.requiredCredentials.join(', ')}</p> : null}
          {job.preferredCredentials?.length ? <p><b>Preferred:</b> {job.preferredCredentials.join(', ')}</p> : null}
          {job.remoteEvidence && <p><b>Remote evidence:</b> {job.remoteEvidence}</p>}
        </section>
      )}
      <section className="detail-section">
        <h3>Score anatomy</h3>
        {scoreLabels.map(([key, label, max]) => <div className="score-line" key={key}><span>{label}</span><div><i style={{ width: `${(job.scoreComponents[key] / max) * 100}%` }}></i></div><b>{job.scoreComponents[key]}/{max}</b></div>)}
      </section>
      <section className="detail-section package-section">
        <div className="section-title"><div><h3>Tailored application package</h3><p>ATS-safe draft, cover letter, keyword map, and screening guidance.</p></div><FileText size={19} /></div>
        <button className="primary wide" disabled={packageBusy} onClick={() => void onGeneratePackage(job)}><WandSparkles size={17} />{packageBusy ? 'Generating…' : job.applicationPackage ? 'Regenerate package' : 'Generate package'}</button>
        {job.applicationPackage && <><div className="package-actions"><button className="secondary" onClick={downloadPackage}><Download size={16} /> Save .md</button><button className="secondary" onClick={() => void navigator.clipboard.writeText(job.applicationPackage || '')}>Copy all</button></div><pre className="package-preview">{job.applicationPackage}</pre></>}
      </section>
      <section className="detail-section">
        <h3>Application evidence</h3>
        <div className="evidence-grid">
          <label>Confirmation #<input className="text-input" value={confirmation} onChange={event => setConfirmation(event.target.value)} /></label>
          <label>Resume / package version<input className="text-input" value={resumeVersion} onChange={event => setResumeVersion(event.target.value)} /></label>
          <label>Follow-up date<input className="text-input" type="date" value={followUpDate.slice(0, 10)} onChange={event => setFollowUpDate(event.target.value)} /></label>
        </div>
        <div className="evidence-actions">
          <button className="secondary" onClick={() => void onUpdate(job, { confirmationNumber: confirmation, resumeVersion, followUpDate })}>Save evidence</button>
          {!job.stopConditions?.length && job.disposition !== 'submitted' && job.disposition !== 'interview' && <button className="primary" onClick={() => void onUpdate(job, { disposition: 'submitted', appliedAt: new Date().toISOString(), confirmationNumber: confirmation, resumeVersion, followUpDate })}>Mark submitted</button>}
        </div>
        <dl>
          <div><dt>Applied</dt><dd>{formatDate(job.appliedAt)}</dd></div>
          <div><dt>Package generated</dt><dd>{formatDate(job.packageGeneratedAt || '')}</dd></div>
        </dl>
        {job.directUrl && <a className="external-link" href={job.directUrl} target="_blank" rel="noreferrer">Open direct application <ChevronRight size={15} /></a>}
      </section>
      {(job.concerns || job.notes) && <section className="detail-section"><h3>Notes</h3>{job.concerns && <p><b>Concern:</b> {job.concerns}</p>}{job.notes && <p>{job.notes}</p>}</section>}
      <button className="danger-button" onClick={() => void onDelete(job)}><Trash2 size={16} /> Delete candidate</button>
    </div>
  );
}

export default App;
