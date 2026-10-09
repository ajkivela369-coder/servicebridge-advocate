import React, { useMemo, useState } from "react";
import { Search, Gauge, Bot, Wrench, GraduationCap, CodeXml, ListTodo, Link2, ShieldCheck, Sparkles, Braces, ChartNoAxesCombined, Clipboard, FileSpreadsheet } from "lucide-react";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { Badge } from "../components/Badge";
import { Progress } from "../components/Progress";
import { ThemeModeSwitch } from "../components/ThemeModeSwitch";
import { FileDropzone } from "../components/FileDropzone";
import { postAudit, type OutputType } from "../endpoints/audit_POST.schema";
import styles from "./_index.module.css";

type View = "overview" | "audit" | "optimizer" | "schema" | "roadmap" | "analytics" | "support" | "training" | "lab" | "evidence";
type SchemaKind = "WebPage" | "Article" | "Course" | "FAQPage";

const issues = [
  { page: "/admissions/md", issue: "Canonical points to legacy URL", level: "Critical", phase: "Now" },
  { page: "/education/programs", issue: "Course schema missing", level: "High", phase: "Now" },
  { page: "/research/neuroscience", issue: "Answer-first summary absent", level: "High", phase: "Next" },
  { page: "/departments/medicine", issue: "Heading hierarchy skips H2", level: "Medium", phase: "Next" },
];

export default function HomePage() {
  const [view, setView] = useState<View>("overview");
  const [url, setUrl] = useState("https://example.edu/programs/medicine");
  const [audit, setAudit] = useState<OutputType | null>(null);
  const [auditError, setAuditError] = useState("");
  const [auditing, setAuditing] = useState(false);
  const [schemaKind, setSchemaKind] = useState<SchemaKind>("WebPage");
  const [csvRows, setCsvRows] = useState(0);

  const nav: Array<[View, string, React.ReactNode]> = [
    ["overview", "Overview", <Gauge size={17}/>],
    ["audit", "URL Auditor", <Search size={17}/>],
    ["optimizer", "Content Optimizer", <Sparkles size={17}/>],
    ["schema", "Schema Studio", <Braces size={17}/>],
    ["roadmap", "Roadmap", <ListTodo size={17}/>],
    ["analytics", "Analytics", <ChartNoAxesCombined size={17}/>],
    ["support", "WordPress Support", <Wrench size={17}/>],
    ["training", "Training", <GraduationCap size={17}/>],
    ["lab", "Technical Lab", <CodeXml size={17}/>],
    ["evidence", "Evidence / Fit", <ShieldCheck size={17}/>],
  ];

  async function runAudit() {
    setAuditing(true);
    setAuditError("");
    try { setAudit(await postAudit({ url })); }
    catch (error) { setAudit(null); setAuditError(error instanceof Error ? error.message : "Audit failed."); }
    finally { setAuditing(false); }
  }

  const schemaJson = useMemo(() => {
    const name = audit?.title || "Example page title";
    const base: Record<string, unknown> = { "@context": "https://schema.org", "@type": schemaKind, name, url: audit?.finalUrl || url };
    if (schemaKind === "Article") Object.assign(base, { headline: name, author: { "@type": "Person", name: "Add verified author" }, dateModified: "YYYY-MM-DD" });
    if (schemaKind === "Course") Object.assign(base, { description: audit?.metaDescription || "Add an accurate course description", provider: { "@type": "Organization", name: "Add institution name" } });
    if (schemaKind === "FAQPage") Object.assign(base, { mainEntity: [{ "@type": "Question", name: "Add a real user question", acceptedAnswer: { "@type": "Answer", text: "Add a concise, source-grounded answer." } }] });
    return JSON.stringify(base, null, 2);
  }, [schemaKind, audit, url]);

  async function importCsv(files: File[]) {
    const text = await files[0]?.text();
    if (!text) return;
    setCsvRows(Math.max(0, text.split(/\r?\n/).filter(Boolean).length - 1));
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}><div className={styles.mark}><Search size={18}/></div><div><strong>SearchSignal</strong><span>SEO + GEO Operations Lab</span></div></div>
        <div className={styles.demo}>Independent portfolio demo</div>
        <nav className={styles.nav}>{nav.map(([id,label,icon])=><Button key={id} variant="ghost" className={styles.navBtn + " " + (view===id?styles.active:"")} onClick={()=>setView(id)}>{icon}{label}</Button>)}</nav>
        <div className={styles.sideNote}><ShieldCheck size={17}/><span>Working, connector-ready, and learning features are labeled separately.</span></div>
      </aside>

      <main className={styles.main}>
        <header className={styles.header}><div><p className={styles.kicker}>Higher-ed web operations</p><h1>{nav.find(([id])=>id===view)?.[1]}</h1></div><div className={styles.actions}><Badge variant="outline">Demo Mode</Badge><ThemeModeSwitch/><Button onClick={()=>setView("audit")}><Search size={16}/> Run Audit</Button></div></header>

        {view==="overview" && <section className={styles.stack}>
          <div className={styles.hero}><div><p className={styles.kicker}>Search + AI visibility strategy</p><h2>Turn a large decentralized web estate into an explainable program of work.</h2><p>Audit traditional SEO and AI-answer readiness, prioritize fixes, support editors, and report progress without pretending unconnected systems are live.</p></div><div className={styles.heroAside}><Bot size={20}/><strong>GEO lens</strong><span>Entity clarity, extractable answers, source signals, structured data, editorial context, and machine-readable page structure.</span></div></div>
          <div className={styles.metrics}><Metric label="URLs audited" value="1,284" note="Seeded demo estate"/><Metric label="SEO health" value="78/100" progress={78} note="+6 after fixes"/><Metric label="GEO readiness" value="69/100" progress={69} note="Explainable rubric"/><Metric label="Critical issues" value="17" note="5 assigned"/><Metric label="Schema coverage" value="58%" progress={58} note="Priority templates"/></div>
          <div className={styles.grid2}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Priority roadmap</p><h3>Highest-leverage findings</h3></div><Button variant="ghost" size="sm" onClick={()=>setView("roadmap")}>Open</Button></div>{issues.map(x=><div className={styles.issue} key={x.page}><div><code>{x.page}</code><strong>{x.issue}</strong></div><Badge variant={x.level==="Critical"?"destructive":x.level==="High"?"warning":"outline"}>{x.level}</Badge><span>{x.phase}</span></div>)}</div><div className={styles.panel}><p className={styles.kicker}>Role coverage</p><h3>Built around the actual job</h3><p className={styles.muted}>SEO/GEO auditing, structured data, content optimization, WordPress support, training, roadmap management, analytics, reporting, and collaboration boundaries.</p><Button variant="outline" onClick={()=>setView("evidence")}>View requirements matrix</Button></div></div>
        </section>}

        {view==="audit" && <section className={styles.stack}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Working surface</p><h2>Live URL Auditor</h2></div><Badge variant="success">Live fetch</Badge></div><p className={styles.muted}>Enter a public HTML page. SearchSignal fetches it server-side, blocks private-network targets, limits redirects and response size, then explains each SEO/GEO score contribution.</p><div className={styles.auditBar}><Input value={url} onChange={e=>setUrl(e.target.value)} aria-label="Public URL"/><Button onClick={runAudit} disabled={auditing}><Search size={16}/> {auditing?"Auditing…":"Analyze page"}</Button></div>{auditError&&<div className={styles.errorBox}>{auditError}</div>}{audit&&<AuditResult audit={audit}/>}</div></section>}

        {view==="optimizer" && <section className={styles.grid2}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Editable drafts only</p><h2>Content Optimizer</h2></div><Badge variant="success">Working demo</Badge></div><Draft label="Suggested title" value={audit?.title && audit.title.length>=30 ? audit.title : (audit?.title || "Program name") + " | Clear audience-focused descriptor"}/><Draft label="Meta description" value={audit?.metaDescription || "Add a concise 120–160 character summary describing the page, audience, and primary value without unsupported claims."}/><Draft label="Answer-first opening" value={"Start with 2–3 sentences that directly define the page topic, who it serves, and the most important verifiable facts before background detail."}/><Draft label="Recommended sections" value={"Overview → Who this is for → Key details → Requirements / process → Frequently asked questions → Sources / contacts"}/></div><div className={styles.panel}><p className={styles.kicker}>AI answer readiness preview</p><h3>What an answer engine should be able to extract</h3><div className={styles.previewAnswer}><strong>{audit?.title || "Page topic"}</strong><p>{audit?.metaDescription || "No reliable summary is currently available from the audited page. Add a concise, source-grounded opening paragraph."}</p><span>Source: {audit?.finalUrl || url}</span></div><p className={styles.muted}>Suggestions are drafts for human review. SearchSignal does not auto-publish content.</p></div></section>}

        {view==="schema" && <section className={styles.grid2}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Structured data</p><h2>Schema Studio</h2></div><Badge variant="success">Local validation</Badge></div><div className={styles.schemaKinds}>{(["WebPage","Article","Course","FAQPage"] as SchemaKind[]).map(kind=><Button key={kind} variant={schemaKind===kind?"primary":"outline"} size="sm" onClick={()=>setSchemaKind(kind)}>{kind}</Button>)}</div><p className={styles.muted}>Use schema only when the visible page content genuinely supports the type and fields. Markup should clarify content, not manufacture facts.</p><div className={styles.validation}><ShieldCheck size={18}/><div><strong>JSON syntax valid</strong><span>Required context and type are present. Verify all draft field values against the page before publishing.</span></div></div></div><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>JSON-LD preview</p><h3>{schemaKind}</h3></div><Button variant="outline" size="sm" onClick={()=>navigator.clipboard.writeText(schemaJson)}><Clipboard size={15}/> Copy</Button></div><pre className={styles.codeBlock}>{schemaJson}</pre></div></section>}

        {view==="roadmap" && <section className={styles.panel}><p className={styles.kicker}>Program management</p><h2>Now / Next / Later roadmap</h2><div className={styles.formula}>Priority model is proprietary; this view exposes decision factors and resulting phases without publishing internal weights.</div><div className={styles.columns}>{["Now","Next","Later"].map(phase=><div key={phase}><h3>{phase}</h3>{issues.filter(x=>x.phase===phase).map(x=><div className={styles.card} key={x.page}><code>{x.page}</code><strong>{x.issue}</strong><span>{x.level} priority · transparent scoring ready</span></div>)}</div>)}</div></section>}

        {view==="analytics" && <section className={styles.stack}><div className={styles.grid2}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Measurement</p><h2>Search visibility reporting</h2></div><Badge variant="outline">Demo data</Badge></div>{[["Impressions","184k","+12%"],["Clicks","14.2k","+8%"],["CTR","7.7%","+0.4"],["Avg. position","11.8","-1.9"]].map(([a,b,c])=><div className={styles.analyticsRow} key={a}><span>{a}</span><strong>{b}</strong><small>{c}</small></div>)}</div><div className={styles.panel}><p className={styles.kicker}>Connector status</p><h3>Use real data only when connected</h3><Connector name="Google Search Console" detail="Connector-ready · not authenticated in this demo"/><Connector name="Google Analytics" detail="Connector-ready · not authenticated in this demo"/></div></div><div className={styles.grid2}><div className={styles.panel}><p className={styles.kicker}>CSV fallback</p><h3>Import an exported report</h3><FileDropzone accept=".csv,text/csv" maxFiles={1} maxSize={2_000_000} onFilesSelected={importCsv} title="Import Search Console / analytics CSV" subtitle="Local browser parse for portfolio demonstration"/>{csvRows>0&&<div className={styles.validation}><FileSpreadsheet size={18}/><div><strong>{csvRows} data rows loaded</strong><span>The imported file stays in this browser session for this demo.</span></div></div>}</div><div className={styles.panel}><p className={styles.kicker}>AI visibility log</p><h3>Manual evidence, not invented automation</h3>{[["ChatGPT","medical education admissions","Mention observed"],["Google AI Overviews","MD curriculum","Not observed"],["Perplexity","health sciences research","Citation observed"]].map(([engine,q,result])=><div className={styles.visibilityRow} key={engine+q}><strong>{engine}</strong><span>{q}</span><Badge variant={result.includes("observed")?"success":"outline"}>{result}</Badge></div>)}</div></div></section>}

        {view==="support" && <section className={styles.grid2}><div className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Support queue</p><h2>WordPress editor support</h2></div><Badge variant="outline">Connector-ready</Badge></div>{[["Admissions","Redirect after page rename"],["Pathology","Image alt text cleanup"],["Student Affairs","Menu publishing issue"],["Research","Template request touches architecture"]].map(([d,t])=><div className={styles.ticket} key={t}><Wrench size={16}/><div><span>{d}</span><strong>{t}</strong></div></div>)}</div><div className={styles.panel}><p className={styles.kicker}>Safe-change boundary</p><h3>Fix what belongs in the editor lane. Escalate architecture.</h3><p className={styles.muted}>Content, headings, links, media, metadata, and basic page structure are editor-support work. Apache, PHP/template architecture, application routing, and risky server changes require Web Architect review.</p><Connector name="WordPress self-hosted" detail="Connector-ready · no production credentials attached"/><Connector name="WordPress.com" detail="Connector-ready · no account attached"/></div></section>}

        {view==="training" && <section className={styles.panel}><p className={styles.kicker}>Distributed editor enablement</p><h2>Training Center</h2><div className={styles.modules}>{["WordPress page editing","Heading hierarchy","Links + redirects","Image alt text","SEO titles + meta","Schema basics","GEO writing","Escalation rules"].map((m,i)=><div className={styles.module} key={m}><GraduationCap size={18}/><strong>{m}</strong><span>{i<3?"Completed":"Lesson · checklist · quiz"}</span><Progress value={i<3?100:25}/></div>)}</div></section>}

        {view==="lab" && <section className={styles.panel}><div className={styles.panelTitle}><div><p className={styles.kicker}>Safe technical learning</p><h2>Technical Lab</h2></div><Badge variant="outline">No production-access claim</Badge></div><div className={styles.modules}>{[["Canonicalization","<link rel='canonical' href='https://example.edu/program' />"],["301 redirects","Redirect 301 /old /new"],["Robots / noindex","<meta name='robots' content='noindex,follow' />"],["Apache boundary","RewriteRule ^old$ /new [R=301,L]"],["WordPress templates","page.php → singular.php → index.php"],["MariaDB basics","SELECT post_title FROM wp_posts;"]].map(([m,c])=><div className={styles.module} key={m}><CodeXml size={18}/><strong>{m}</strong><code>{c}</code></div>)}</div></section>}

        {view==="evidence" && <section className={styles.panel}><p className={styles.kicker}>Truth-labeled portfolio evidence</p><h2>Requirements Coverage</h2><p className={styles.muted}>This project is an independent capability demonstration. It distinguishes implemented functionality, connector-ready integrations, and safe technical-learning examples.</p>{[["SEO/GEO auditing","Working"],["Content optimization workflow","Working"],["Structured data/schema","Working"],["Prioritized roadmap","Working"],["Analytics CSV workflow","Working"],["Google Search Console + Analytics","Connector-ready"],["WordPress multisite support","Connector-ready"],["Apache / PHP / MariaDB","Technical lab"]].map(([a,b])=><div className={styles.coverage} key={a}><strong>{a}</strong><Badge variant={b==="Working"?"success":"outline"}>{b}</Badge></div>)}<div className={styles.links}><Button variant="outline" onClick={()=>window.open("https://aj-kivela-portfolio.lovable.app/","_blank")}><Link2 size={16}/> Portfolio</Button><span className={styles.muted}>Source code is private; selected implementation details can be reviewed by screen share.</span></div></section>}

        <footer className={styles.footer}>© 2026 Alexander J. Kivela. Proprietary portfolio software. All rights reserved. Independent portfolio demonstration. Analysis of a public site does not imply affiliation with or endorsement by that organization.</footer>
      </main>
    </div>
  );
}

function Metric({label,value,note,progress}:{label:string;value:string;note:string;progress?:number}){return <div className={styles.metric}><span>{label}</span><strong>{value}</strong>{progress!==undefined&&<Progress value={progress}/>}<small>{note}</small></div>}
function Score({label,value}:{label:string;value:string}){return <div className={styles.score}><span>{label}</span><strong>{value}</strong><small>/100</small></div>}
function Draft({label,value}:{label:string;value:string}){return <div className={styles.draft}><span>{label}</span><p>{value}</p></div>}
function Connector({name,detail}:{name:string;detail:string}){return <div className={styles.connector}><div><strong>{name}</strong><span>{detail}</span></div><Badge variant="outline">Connect / import</Badge></div>}
function AuditResult({audit}:{audit:OutputType}){
  const variant=(status:string)=>status==="critical"?"destructive":status==="high"?"warning":status==="pass"?"success":"outline";
  return <div className={styles.result}><div className={styles.resultMeta}><div><span>Fetched</span><code>{audit.finalUrl}</code></div><Badge variant={audit.wordpressDetected?"secondary":"outline"}>{audit.wordpressDetected?"WordPress detected":"CMS not identified"}</Badge></div><div className={styles.scores}><Score label="SEO" value={String(audit.seoScore)}/><Score label="GEO" value={String(audit.geoScore)}/><div className={styles.score}><span>Words</span><strong>{audit.wordCount}</strong></div></div>{audit.checks.map(check=><div className={styles.check} key={check.key}><div><strong>{check.label}</strong><span>{check.finding}</span><small>{check.why} · {check.points}/{check.maxPoints} pts</small></div><Badge variant={variant(check.status) as "destructive"|"warning"|"success"|"outline"}>{check.status}</Badge></div>)}</div>;
}
  117
