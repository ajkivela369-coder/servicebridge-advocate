const state={lastAudit:null,caseStudyUrl:'https://geiselmed.dartmouth.edu/'};

const pages=[
  ['dashboard','Dashboard'],
  ['interview','Geisel Interview Mode'],
  ['auditor','Live URL Auditor'],
  ['site','Site Intelligence'],
  ['optimizer','Content Optimizer'],
  ['schema','Structured Data Studio'],
  ['roadmap','Priority Roadmap'],
  ['analytics','Analytics & AI Visibility'],
  ['wordpress','WordPress Support'],
  ['training','Training Center'],
  ['lab','Technical Lab'],
  ['coverage','Requirements Coverage']
];

const nav=document.getElementById('nav');
const view=document.getElementById('view');
const navIcons={
  dashboard:'nav-dashboard.svg',interview:'nav-interview.svg',auditor:'nav-auditor.svg',site:'nav-roadmap.svg',
  optimizer:'nav-optimizer.svg',schema:'nav-schema.svg',roadmap:'nav-roadmap.svg',
  analytics:'nav-analytics.svg',wordpress:'nav-wordpress.svg',training:'nav-training.svg',
  lab:'nav-lab.svg',coverage:'nav-coverage.svg'
};

for(const p of pages){
  const b=document.createElement('button');
  b.innerHTML='<img class="nav-icon" src="/assets/ui/'+navIcons[p[0]]+'" alt="" aria-hidden="true"><span>'+esc(p[1])+'</span>';
  b.dataset.page=p[0];
  b.onclick=()=>show(p[0]);
  nav.appendChild(b);
}

document.body.addEventListener('click',(e)=>{
  const target=e.target.closest('[data-go]');
  if(target) show(target.dataset.go);
});

function esc(s){return String(s??'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function setTitle(name,lead){document.getElementById('pageTitle').textContent=name;document.getElementById('pageLead').textContent=lead;}
function setActive(id){document.querySelectorAll('nav button').forEach((b)=>b.classList.toggle('active',b.dataset.page===id));}
function kpi(label,value,note,icon=''){return '<div class="card kpi-card">'+(icon?'<img class="kpi-icon" src="/assets/ui/'+icon+'" alt="" aria-hidden="true">':'')+'<div class="muted mini kpi-label">'+label+'</div><div class="metric">'+value+'</div><div class="muted mini">'+note+'</div></div>';}
function status(kind,text){return '<span class="status '+kind+'">'+text+'</span>';}

function show(id){
  setActive(id);
  const routes={dashboard,interview,auditor,site:siteIntelligence,optimizer,schemaStudio,roadmap,analytics,wordpress,training,lab,coverage};
  (routes[id]||dashboard)();
  window.scrollTo(0,0);
}

function dashboard(){
  setTitle('Operations Dashboard','Search visibility, AI readiness, and support work in one accountable workspace.');
  view.innerHTML=
    '<div class="grid kpis">'+
      kpi('URLs audited','1,284','demo dataset','kpi-link.svg')+
      kpi('SEO health','82','weighted checks','kpi-pulse.png')+
      kpi('GEO readiness','74','answer-engine rubric','kpi-target.png')+
      kpi('Critical issues','17','requires triage','kpi-warning.png')+
      kpi('Schema coverage','63%','priority pages','kpi-layers.png')+
    '</div>'+
    '<div class="grid two section" style="margin-top:16px">'+
      '<div class="card"><h2>Priority roadmap</h2><table><tr><th>Subsite</th><th>Finding</th><th>Phase</th><th>Owner</th></tr>'+
      '<tr><td>Admissions</td><td>Duplicate program titles + weak canonicals</td><td>Now</td><td>Web</td></tr>'+
      '<tr><td>Research</td><td>Faculty pages missing Person schema</td><td>Now</td><td>Comms</td></tr>'+
      '<tr><td>Student Affairs</td><td>Thin landing pages / weak internal links</td><td>Next</td><td>Dept.</td></tr>'+
      '<tr><td>News</td><td>Article author/date markup inconsistent</td><td>Later</td><td>Editors</td></tr></table></div>'+
      '<div class="card"><h2>Operating model</h2><p><b>Reactive:</b> WordPress support, broken links, redirects, publishing help.</p><p><b>Proactive:</b> technical audits, GEO improvements, schema, internal linking, reporting.</p><div class="callout">Every score is explainable. Recommendations are tied to observable evidence or clearly labeled demo data.</div></div>'+
    '</div>';
}

function interview(){
  setTitle('Geisel Interview Mode','A five-minute public-data case study: inspect → prioritize → support → measure.');
  const d=state.lastAudit;
  const auditState=d?status('work','Live audit completed'):status('ready','Ready to run');
  const auditDetail=d
    ? '<b>'+esc(d.title||'Audited page')+'</b><div class="muted mini">SEO '+d.scores.seo+'/100 · GEO '+d.scores.geo+'/100 · '+d.findings.length+' findings</div>'
    : '<b>Geisel public homepage</b><div class="muted mini">No internal systems or private data required.</div>';
  view.innerHTML=
    '<div class="card section"><div class="eyebrow">INTERVIEW CASE STUDY</div><h2>How I would approach Geisel\'s web-visibility work</h2><p>Start with observable evidence, rank the work transparently, make safe changes, help content owners, then measure whether the change helped.</p><div class="header-actions"><button id="startCaseAudit" class="primary">1. Run live public-page audit</button><button data-go="site" class="secondary">2. Run bounded site scan</button><button data-go="roadmap" class="secondary">3. Open prioritization engine</button></div><p class="muted mini">Independent portfolio demonstration. Public data only; no Dartmouth credentials, analytics access, or production administration is implied.</p></div>'+
    '<div class="grid three section">'+
      '<div class="card"><div class="stepnum">01</div><h3>Inspect</h3>'+auditState+'<p>'+auditDetail+'</p><p class="muted">Technical SEO, content structure, schema, links, accessibility signals, and AI-answer extractability.</p></div>'+
      '<div class="card"><div class="stepnum">02</div><h3>Prioritize</h3>'+status('work','Working model')+'<p><b>Why this work first?</b></p><p class="muted">Balance visibility gap, competition, demand/capacity pressure, institutional impact, staff capacity, and implementation effort.</p></div>'+
      '<div class="card"><div class="stepnum">03</div><h3>Fix safely</h3>'+status('work','Defined boundary')+'<p><b>Page-level work vs. escalation</b></p><p class="muted">Handle content, metadata, links, media and approved redirects; escalate risky server, authentication, theme/PHP, and architecture changes.</p></div>'+
    '</div>'+
    '<div class="grid two section">'+
      '<div class="card"><h2>04 · Support the people maintaining the site</h2><p>Translate technical findings into plain-language actions for faculty and staff, then leave behind training that prevents the same problem from recurring.</p><button data-go="wordpress" class="secondary">WordPress support workflow</button> <button data-go="training" class="secondary">Training center</button></div>'+
      '<div class="card"><h2>05 · Measure and report</h2><p>Show what changed, what evidence supports it, what still needs attention, and whether search or AI visibility moved afterward.</p><button data-go="analytics" class="secondary">Measurement workspace</button></div>'+
    '</div>'+
    '<div class="card section"><h2>First 90 days — interview discussion draft</h2><table><tr><th>Period</th><th>Focus</th><th>Evidence of progress</th></tr><tr><td>Days 1–30</td><td>Inventory, baselines, stakeholder map, urgent defects, support intake.</td><td>Repeatable audit + triage process; clear ownership and escalation paths.</td></tr><tr><td>Days 31–60</td><td>Priority-page SEO/GEO improvements, redirects, schema, internal linking, editor training.</td><td>Completed changes tied to before/after evidence and documented decisions.</td></tr><tr><td>Days 61–90</td><td>Scale the workflow, refine reporting, identify recurring support issues, expand successful patterns.</td><td>Transparent backlog, reusable training, trend reporting, and a defensible next-quarter roadmap.</td></tr></table><p class="muted mini">This is an interview planning framework, not a claim about Geisel\'s internal priorities or systems.</p></div>';
  document.getElementById('startCaseAudit').onclick=()=>{
    show('auditor');
    setTimeout(()=>{
      const input=document.getElementById('auditUrl');
      if(input) input.value=state.caseStudyUrl;
      const button=document.getElementById('auditBtn');
      if(button) button.click();
    },0);
  };
}

function auditor(){
  setTitle('Live URL Auditor','Inspect a public page for technical SEO and AI-answer readiness with transparent scoring.');
  view.innerHTML=
    '<div class="card section"><h2>Audit a public page</h2>'+
      '<div class="form-row"><input id="auditUrl" value="https://geiselmed.dartmouth.edu/" aria-label="URL"><button id="auditBtn" class="primary">Run audit</button></div>'+
      '<p class="muted mini">Server-side fetch with private-network blocking, redirect checks, timeout, HTML-only validation, and a 2 MB response limit.</p>'+
    '</div><div id="auditOut"></div>';
  document.getElementById('auditBtn').onclick=runAudit;
}

async function runAudit(){
  const btn=document.getElementById('auditBtn');
  const out=document.getElementById('auditOut');
  btn.disabled=true; btn.textContent='Auditing…';
  out.innerHTML='<div class="card">Fetching and inspecting page…</div>';
  try{
    const response=await fetch('/api/audit',{
      method:'POST',
      headers:{'content-type':'application/json'},
      body:JSON.stringify({url:document.getElementById('auditUrl').value})
    });
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||'Audit failed');
    state.lastAudit=data;
    renderAudit(data);
  }catch(error){
    out.innerHTML='<div class="card"><h2>Audit error</h2><p>'+esc(error.message)+'</p></div>';
  }finally{
    btn.disabled=false; btn.textContent='Run audit';
  }
}

function checks(list){
  return list.map((c)=>'<div class="check"><span class="'+(c.ok?'ok':'bad')+'">'+(c.ok?'✓':'×')+'</span><span>'+esc(c.name)+'</span><span>'+c.weight+'pt</span></div>').join('');
}

function renderAudit(d){
  const rows=d.findings.map((f)=>'<tr><td><span class="sev '+f.severity+'">'+f.severity+'</span></td><td><b>'+esc(f.label)+'</b><div class="muted mini">'+esc(f.evidence)+'</div></td><td>'+esc(f.fix)+'</td></tr>').join('');
  document.getElementById('auditOut').innerHTML=
    '<div class="grid two section">'+
      '<div class="card"><h2>SEO health</h2><div class="scoreline"><div class="score">'+d.scores.seo+'</div><div><b>'+esc(d.title||'Untitled page')+'</b><div class="muted">'+esc(d.finalUrl)+'</div></div></div>'+checks(d.rubrics.seo)+'</div>'+
      '<div class="card"><h2>GEO readiness</h2><div class="scoreline"><div class="score">'+d.scores.geo+'</div><div><b>AI-answer extraction signals</b><div class="muted">'+d.wordCount+' words · '+d.schema.types.length+' schema type(s)</div></div></div>'+checks(d.rubrics.geo)+'</div>'+
    '</div>'+
    '<div class="grid three section">'+
      kpi('Internal links',d.links.internal,d.links.total+' total links')+
      kpi('Alt coverage',d.images.coverage+'%',d.images.withAlt+'/'+d.images.total+' images')+
      kpi('WordPress',d.signals.wordpress?'Likely':'Not detected',esc(d.signals.generator||'fingerprint check'))+
    '</div>'+
    '<div class="card section"><h2>Findings & recommended fixes</h2><table><tr><th>Priority</th><th>Evidence</th><th>Recommendation</th></tr>'+rows+'</table>'+
      '<div style="margin-top:12px"><button class="secondary" id="copyAudit">Copy plain-language summary</button></div>'+
    '</div>';
  document.getElementById('copyAudit').onclick=function(){
    navigator.clipboard.writeText(auditSummary(d));
    this.textContent='Copied';
  };
}

function auditSummary(d){
  return 'SearchSignal audit: '+d.finalUrl+'\nSEO '+d.scores.seo+'/100 · GEO '+d.scores.geo+'/100\n'+d.findings.map((f)=>f.severity+': '+f.label+' — '+f.fix).join('\n');
}

function siteIntelligence(){
  setTitle('Site Intelligence','Run a bounded same-site crawl, inventory linked documents, and validate redirect chains.');
  view.innerHTML=
    '<div class="grid two section">'+
      '<div class="card"><h2>Bounded site scan</h2><p class="muted">Crawls public HTML on the same origin only. Query strings are removed to reduce duplicate/infinite crawl paths; the demo is capped at 12 pages.</p><div class="form-row"><input id="siteUrl" value="'+esc(state.caseStudyUrl)+'" aria-label="Starting URL"><select id="siteLimit" style="max-width:120px" aria-label="Page limit"><option>4</option><option selected>6</option><option>8</option><option>10</option><option>12</option></select><button id="siteScanBtn" class="primary">Scan site</button></div></div>'+
      '<div class="card"><h2>Redirect validator</h2><p class="muted">Follows up to eight public redirects and shows every HTTP hop before the final destination.</p><div class="form-row"><input id="redirectUrl" value="'+esc(state.caseStudyUrl)+'" aria-label="URL to validate"><button id="redirectBtn" class="secondary">Check chain</button></div><div id="redirectOut" class="muted mini" style="margin-top:10px">No redirect check run.</div></div>'+
    '</div><div id="siteScanOut"></div>';
  document.getElementById('siteScanBtn').onclick=runSiteScan;
  document.getElementById('redirectBtn').onclick=runRedirectCheck;
}

async function runSiteScan(){
  const button=document.getElementById('siteScanBtn');
  const out=document.getElementById('siteScanOut');
  button.disabled=true;button.textContent='Scanning…';
  out.innerHTML='<div class="card">Crawling a small same-origin sample and checking linked documents…</div>';
  try{
    const response=await fetch('/api/site-scan',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({url:document.getElementById('siteUrl').value,limit:Number(document.getElementById('siteLimit').value)})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||'Site scan failed');
    state.lastSiteScan=data;
    renderSiteScan(data);
  }catch(error){
    out.innerHTML='<div class="card"><h2>Site scan error</h2><p>'+esc(error.message)+'</p></div>';
  }finally{button.disabled=false;button.textContent='Scan site';}
}

function renderSiteScan(d){
  const s=d.summary;
  const pageRows=d.pages.map((p)=>'<tr><td><span class="sev '+(p.error?'High':'Opportunity')+'">'+(p.error?'Error':p.status)+'</span></td><td><b>'+esc(p.title||'(untitled)')+'</b><div class="muted mini">'+esc(p.url)+'</div>'+(p.error?'<div class="muted mini">'+esc(p.error)+'</div>':'')+'</td><td>'+(p.error?'—':p.h1Count)+'</td><td>'+(p.error?'—':p.wordCount)+'</td><td>'+(p.error?'—':(p.description?'Yes':'No'))+'</td><td>'+(p.error?'—':(p.canonical?'Yes':'No'))+'</td></tr>').join('');
  const docRows=d.documents.map((x)=>'<tr><td>'+(x.error?'Error':x.status)+'</td><td><b>'+esc(x.linkText)+'</b><div class="muted mini">'+esc(x.url)+'</div></td><td>'+esc(x.contentType||'unknown')+'</td><td>'+(x.bytes?Math.round(x.bytes/1024)+' KB':'—')+'</td><td><span class="muted mini">'+esc(x.source)+'</span></td></tr>').join('');
  document.getElementById('siteScanOut').innerHTML=
    '<div class="grid kpis section">'+
      kpi('Pages crawled',s.pagesCrawled,s.pageErrors+' fetch error(s)')+
      kpi('Missing descriptions',s.missingDescriptions,'sampled pages')+
      kpi('H1 issues',s.h1Issues,'not exactly one H1')+
      kpi('Documents found',s.documentsFound,s.documentsChecked+' checked')+
      kpi('Average words',s.averageWords,'successful pages')+
    '</div>'+
    '<div class="card section"><div class="header-actions" style="justify-content:space-between"><div><h2>Page inventory</h2><p class="muted mini">This is a bounded sample, not a claim of complete estate coverage.</p></div><button id="downloadScan" class="secondary">Download JSON evidence</button></div><div class="table-wrap"><table><tr><th>Status</th><th>Page</th><th>H1</th><th>Words</th><th>Description</th><th>Canonical</th></tr>'+pageRows+'</table></div></div>'+
    '<div class="card section"><h2>Linked document inventory</h2>'+(docRows?'<div class="table-wrap"><table><tr><th>Status</th><th>Document / link text</th><th>Type</th><th>Size</th><th>Found on</th></tr>'+docRows+'</table></div>':'<p class="muted">No PDF/Office document links were discovered in this crawl sample.</p>')+'</div>'+
    '<div class="callout section"><b>Architecture signals:</b> '+s.missingTitles+' missing title(s), '+s.missingDescriptions+' missing description(s), '+s.missingCanonicals+' missing canonical(s), '+s.noindexPages+' noindex page(s), and '+s.h1Issues+' H1 structure issue(s) in the sampled pages.</div>';
  document.getElementById('downloadScan').onclick=()=>{
    const blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='searchsignal-site-scan.json';a.click();URL.revokeObjectURL(url);
  };
}

async function runRedirectCheck(){
  const button=document.getElementById('redirectBtn');
  const out=document.getElementById('redirectOut');
  button.disabled=true;button.textContent='Checking…';
  try{
    const response=await fetch('/api/redirect-check',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({url:document.getElementById('redirectUrl').value})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||'Redirect check failed');
    out.innerHTML='<b>'+data.hops+' redirect hop(s)</b><div class="redirect-chain">'+data.chain.map((x,i)=>'<div class="check"><span class="'+(i===data.chain.length-1&&x.status<400?'ok':'')+'">'+x.status+'</span><span>'+esc(x.url)+(x.location?'<div class="muted mini">→ '+esc(x.location)+'</div>':'')+'</span><span>'+(i===data.chain.length-1?'final':'hop')+'</span></div>').join('')+'</div>';
  }catch(error){out.innerHTML='<span class="bad">'+esc(error.message)+'</span>';}
  finally{button.disabled=false;button.textContent='Check chain';}
}

function optimizer(){
  setTitle('Content Optimizer','Turn page evidence into editable search + AI-answer recommendations.');
  const seed=state.lastAudit?(state.lastAudit.description||state.lastAudit.title):'';
  view.innerHTML=
    '<div class="grid two">'+
      '<div class="card"><h2>Page copy or summary</h2><textarea id="copy">'+esc(seed)+'</textarea><button class="primary" id="optBtn" style="margin-top:9px">Generate draft recommendations</button></div>'+
      '<div class="card" id="optOut"><h2>AI answer readiness preview</h2><p class="muted">Recommendations appear here. They are drafts only and are never published automatically.</p></div>'+
    '</div>';
  document.getElementById('optBtn').onclick=()=>{
    const text=document.getElementById('copy').value.trim();
    const first=text.split(/[.!?]/)[0].slice(0,155);
    document.getElementById('optOut').innerHTML=
      '<h2>Editable draft</h2>'+
      '<p><b>Answer-first opening:</b> '+esc(first+(first?'.':''))+'</p>'+
      '<p><b>Suggested outline:</b> What this page covers → key facts → process/requirements → FAQs → sources/contact.</p>'+
      '<p><b>GEO additions:</b> explicit entity naming, updated date, responsible author/editor, source links, concise Q&A blocks, truthful structured data.</p>'+
      '<p><b>SEO additions:</b> unique title, descriptive meta, one H1, descriptive internal links, meaningful alt text, canonical review.</p>'+
      '<div class="callout">Draft guidance only. A human editor should verify facts, claims, accessibility, and institutional policy before publication.</div>';
  };
}

function schemaStudio(){
  setTitle('Structured Data Studio','Generate and validate transparent JSON-LD drafts.');
  view.innerHTML=
    '<div class="grid two">'+
      '<div class="card"><h2>Schema builder</h2>'+
        '<label>Type<select id="schemaType" class="field"><option>WebPage</option><option>Article</option><option>FAQPage</option><option>BreadcrumbList</option><option>Organization</option><option>Person</option><option>Course</option><option>MedicalWebPage</option></select></label><br>'+
        '<label>Name<input id="schemaName" class="field" placeholder="Page or entity name"></label><br>'+
        '<label>URL<input id="schemaUrl" class="field" placeholder="https://example.edu/page"></label><br>'+
        '<label>Description<textarea id="schemaDesc" placeholder="Plain-language description"></textarea></label>'+
        '<button id="schemaBtn" class="primary">Generate JSON-LD</button>'+
      '</div>'+
      '<div class="card"><h2>Preview & validation</h2><pre id="schemaOut">{}</pre><p id="schemaNote" class="muted mini">Use schema only when it accurately reflects visible page content.</p><button class="secondary" id="copySchema">Copy JSON-LD</button></div>'+
    '</div>';
  const build=()=>{
    const type=document.getElementById('schemaType').value;
    const data={'@context':'https://schema.org','@type':type,name:document.getElementById('schemaName').value,url:document.getElementById('schemaUrl').value,description:document.getElementById('schemaDesc').value};
    Object.keys(data).forEach((k)=>{if(data[k]==='')delete data[k];});
    document.getElementById('schemaOut').textContent=JSON.stringify(data,null,2);
    document.getElementById('schemaNote').textContent=data.name&&data.url?'Syntax valid. Review schema-type-specific required/recommended properties before production.':'Add at least a name and URL for a stronger draft.';
  };
  document.getElementById('schemaBtn').onclick=build;
  document.getElementById('copySchema').onclick=()=>navigator.clipboard.writeText(document.getElementById('schemaOut').textContent);
}

function roadmap(){
  setTitle('Priority Roadmap','Turn competing requests into a transparent, defensible sequence of work.');
  const areas=[
    {area:'Admissions',work:'Program discovery + conversion path',impact:5,gap:4,competition:5,demand:5,staff:3,effort:2},
    {area:'Research',work:'Faculty + research discoverability',impact:4,gap:4,competition:4,demand:3,staff:3,effort:3},
    {area:'Student Affairs',work:'Navigation + internal linking',impact:4,gap:3,competition:3,demand:4,staff:2,effort:3},
    {area:'News',work:'Author/date + Article schema consistency',impact:3,gap:3,competition:2,demand:2,staff:4,effort:2},
    {area:'Legacy PDFs',work:'Metadata + discoverability cleanup',impact:4,gap:5,competition:2,demand:3,staff:2,effort:4}
  ];
  const factors=[
    ['impact','Impact'],['gap','Visibility gap'],['competition','Competition'],
    ['demand','Demand / capacity pressure'],['staff','Dept. web capacity'],['effort','Effort']
  ];
  const score=(a)=>{
    const supportNeed=6-a.staff;
    return (a.impact*2)+(a.gap*1.5)+a.competition+(a.demand*1.5)+supportNeed-(a.effort*1.25);
  };
  const phase=(s)=>s>=24?'Now':s>=18?'Next':'Later';
  const cell=(a,i,f)=>'<input class="prio-input" type="number" min="1" max="5" value="'+a[f]+'" data-i="'+i+'" data-f="'+f+'" aria-label="'+f+' for '+esc(a.area)+'">';
  view.innerHTML=
    '<div class="callout section"><b>Transparent model:</b> Impact ×2 + visibility gap ×1.5 + competition + demand/capacity pressure ×1.5 + support need − effort ×1.25. Department web capacity is inverted into support need, so low-capacity teams receive more weight. Every input is editable.</div>'+
    '<div class="card section"><h2>Interview scenario inputs</h2><p class="muted">These starting values are illustrative—not Geisel internal data. In practice I would replace them with stakeholder priorities, Search Console/Analytics evidence, service demand, and available staff capacity.</p></div>'+
    '<div class="table-wrap"><table><thead><tr><th>Area</th><th>Work</th>'+factors.map((f)=>'<th>'+f[1]+'<div class="muted mini">1–5</div></th>').join('')+'<th>Phase</th><th>Score</th></tr></thead><tbody id="roadmapRows"></tbody></table></div>'+
    '<div class="section" style="margin-top:12px"><button class="secondary" id="copyRoadmap">Copy ranked roadmap</button> <button class="secondary" data-go="interview">Back to interview mode</button></div>';
  const render=()=>{
    const ranked=areas.map((a,i)=>({a,i,s:score(a)})).sort((x,y)=>y.s-x.s);
    document.getElementById('roadmapRows').innerHTML=ranked.map(({a,i,s})=>
      '<tr><td><b>'+esc(a.area)+'</b></td><td>'+esc(a.work)+'</td>'+
      factors.map((f)=>'<td>'+cell(a,i,f[0])+'</td>').join('')+
      '<td><span class="phase '+phase(s).toLowerCase()+'">'+phase(s)+'</span></td><td><b>'+s.toFixed(1)+'</b></td></tr>'
    ).join('');
    document.querySelectorAll('.prio-input').forEach((input)=>{
      input.onchange=()=>{
        const i=Number(input.dataset.i);
        const f=input.dataset.f;
        areas[i][f]=Math.max(1,Math.min(5,Number(input.value)||1));
        render();
      };
    });
  };
  render();
  document.getElementById('copyRoadmap').onclick=function(){
    const ranked=areas.map((a)=>({a,s:score(a)})).sort((x,y)=>y.s-x.s);
    const text=['SearchSignal priority roadmap — illustrative inputs']
      .concat(ranked.map((x,n)=>(n+1)+'. '+x.a.area+' — '+x.a.work+' — '+phase(x.s)+' — '+x.s.toFixed(1)))
      .join('\n');
    navigator.clipboard.writeText(text);
    this.textContent='Copied';
  };
}

function analytics(){
  setTitle('Analytics & AI Visibility','Measure impact without pretending unconnected data is live.');
  view.innerHTML=
    '<div class="grid three section">'+
      '<div class="card"><h3>Google Search Console</h3>'+status('ready','CSV import')+'<p class="muted">Queries, pages, impressions, clicks, CTR and average position.</p><input id="gscFile" type="file" accept=".csv,text/csv" hidden><button id="gscImport" class="secondary">Import CSV</button><div id="gscResult" class="muted mini" style="margin-top:9px">No file imported.</div></div>'+
      '<div class="card"><h3>Google Analytics</h3>'+status('ready','CSV import')+'<p class="muted">Organic sessions, landing pages and before/after trend analysis.</p><input id="gaFile" type="file" accept=".csv,text/csv" hidden><button id="gaImport" class="secondary">Import CSV</button><div id="gaResult" class="muted mini" style="margin-top:9px">No file imported.</div></div>'+
      '<div class="card"><h3>AI visibility log</h3>'+status('work','Working demo')+'<p class="muted">Record engine, query, citation/mention, date and source URL without inventing automated measurement.</p><div class="callout">Manual evidence is intentional here: capture engine, query, date, whether Geisel was cited/mentioned, and the source URL.</div></div>'+
    '</div>'+
    '<div class="card"><h2>Demo performance trend</h2><table><tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Change</th></tr><tr><td>Organic clicks</td><td>8,420</td><td>9,615</td><td>+14.2%</td></tr><tr><td>CTR</td><td>3.8%</td><td>4.4%</td><td>+0.6 pp</td></tr><tr><td>Pages with valid schema</td><td>49%</td><td>63%</td><td>+14 pp</td></tr></table><p class="muted mini">Sample data for interface demonstration only. Imported CSV files are read locally in the browser and are not uploaded by this demo.</p></div>';
  const wireCsv=(buttonId,inputId,resultId)=>{
    const button=document.getElementById(buttonId);
    const input=document.getElementById(inputId);
    const result=document.getElementById(resultId);
    button.onclick=()=>input.click();
    input.onchange=async()=>{
      const file=input.files?.[0];
      if(!file){result.textContent='No file imported.';return;}
      const text=await file.text();
      const lines=text.split(/\r?\n/).filter((x)=>x.trim().length);
      const headers=(lines[0]||'').split(',').map((x)=>x.trim()).filter(Boolean);
      result.textContent=file.name+' · '+Math.max(0,lines.length-1)+' data row(s) · '+headers.length+' column(s): '+headers.slice(0,6).join(', ')+(headers.length>6?'…':'');
    };
  };
  wireCsv('gscImport','gscFile','gscResult');
  wireCsv('gaImport','gaFile','gaResult');
}

function wordpress(){
  setTitle('WordPress Support Center','Balance end-user support with safe escalation for architecture and server changes.');
  view.innerHTML=
    '<div class="grid two section">'+
      '<div class="card ticket"><h2>Open support queue</h2><table><tr><th>Priority</th><th>Department</th><th>Request</th></tr><tr><td>High</td><td>Admissions</td><td>Program page redirect loop</td></tr><tr><td>Medium</td><td>Research</td><td>Faculty profile image + alt text</td></tr><tr><td>Low</td><td>Education</td><td>Heading hierarchy cleanup</td></tr><tr><td>Low</td><td>Admin</td><td>Editor training / publishing workflow</td></tr></table></div>'+
      '<div class="card"><h2>Safe change boundary</h2><p><b>Handle directly:</b> page editing, content structure, links, media, alt text, approved redirects, metadata, documentation and training.</p><p><b>Escalate:</b> server config, Apache routing, application-layer changes, risky PHP/theme changes, authentication and multisite architecture.</p><div class="callout warn">This demo does not claim live WordPress admin access.</div></div>'+
    '</div>'+
    '<div class="grid two"><div class="card"><h3>Self-hosted WordPress</h3>'+status('ready','Connector-ready')+'<p class="muted">Designed for authenticated site/content workflows when a real account is connected.</p></div><div class="card"><h3>WordPress.com</h3>'+status('ready','Connector-ready')+'<p class="muted">Separate integration path; no fake connection state.</p></div></div>';
}

function training(){
  setTitle('Training Center','Plain-language support materials for faculty, staff, and distributed content editors.');
  const modules=[
    ['WordPress page editing basics','Use preview, revisions, semantic blocks and clear ownership.'],
    ['Heading hierarchy','One page-level H1; use H2/H3 to express real information structure.'],
    ['Links & redirects','Prefer descriptive link text; distinguish content changes from server-level routing.'],
    ['Image alt text','Describe the information conveyed, not decorative detail.'],
    ['SEO titles & metadata','Unique, specific and useful to humans before algorithms.'],
    ['Schema basics','Markup must match visible content and should never manufacture facts.'],
    ['GEO writing','Lead with clear answers, explicit entities, evidence, dates and source context.'],
    ['Escalation rules','Know when a page-level fix becomes an architecture, security or server issue.']
  ];
  view.innerHTML='<div class="grid two">'+modules.map((m,i)=>'<div class="card module"><details '+(i===0?'open':'')+'><summary>'+m[0]+'</summary><p>'+m[1]+'</p><p class="mini"><b>Mini-check:</b> Can the editor explain why this change improves clarity, accessibility, search visibility, or safe governance?</p></details></div>').join('')+'</div>';
}

function lab(){
  setTitle('Technical Lab','Practice the implementation concepts behind the role without claiming production admin access.');
  view.innerHTML=
    '<div class="grid two">'+
      '<div class="card"><h2>301 vs 302</h2>'+status('lab','Learning lab')+'<p><b>301:</b> permanent move; commonly used when a URL should consolidate long-term signals.</p><p><b>302:</b> temporary move; appropriate when the original URL should remain the intended canonical destination.</p><pre>Redirect 301 /old-page /new-page</pre></div>'+
      '<div class="card"><h2>Canonicalization</h2><p>Canonical tags communicate the preferred representative URL for duplicate or near-duplicate content.</p><pre>&lt;link rel="canonical" href="https://example.edu/preferred-page"&gt;</pre></div>'+
      '<div class="card"><h2>Apache / .htaccess boundary</h2><p>Page-level recommendations can be prepared here, but server directives should be reviewed with the Web Architect in a hybrid files-first environment.</p><pre>RewriteRule ^old-path$ /new-path [R=301,L]</pre></div>'+
      '<div class="card"><h2>WordPress + data layer</h2><p>Template hierarchy, PHP safety, and MariaDB/MySQL concepts are represented as technical-learning surfaces, not fabricated production experience.</p><pre>content → template → application layer → database\n         ↘ static files / Apache routing</pre></div>'+
    '</div>';
}

function coverage(){
  setTitle('Requirements Coverage','A defensible map from job responsibilities to concrete portfolio evidence.');
  const rows=[
    ['Technical/content SEO audits','Live URL Auditor inspects crawl/index, metadata, canonical, headings, links, alt text and schema.',status('work','Working')],
    ['Site crawl / documents / redirects','Site Intelligence crawls a bounded same-origin sample, inventories linked PDF/Office documents, and traces redirect chains.',status('work','Working')],
    ['GEO / AI visibility','Explainable GEO rubric for answer-first structure, entities, citations, authorship, dates and extractability.',status('work','Working')],
    ['Structured data','JSON-LD studio plus live schema detection/validation signals.',status('work','Working')],
    ['Prioritized phased roadmap','Transparent impact/reach/confidence/effort model with Now / Next / Later planning.',status('work','Working')],
    ['Search Console / Analytics','Browser-local CSV import is working; authenticated account connections remain intentionally unconnected.',status('work','CSV workflow')],
    ['WordPress support','Ticket workflow, page-level support model, safe change boundary and escalation logic.',status('work','Working demo')],
    ['WordPress admin integration','Prepared as an authenticated connector path; not represented as live.',status('ready','Connector-ready')],
    ['WordPress Multisite lab','Local Apache/PHP/MariaDB acceptance artifacts document hands-on Multisite practice without presenting it as production employment.',status('lab','Validated lab')],
    ['Training & documentation','Eight mini training modules with plain-language guidance and escalation rules.',status('work','Working')],
    ['Apache / PHP / MariaDB literacy','Interactive learning lab demonstrates concepts and safe escalation boundary.',status('lab','Learning lab')],
    ['Large decentralized environment','Dashboard + roadmap + ownership/status patterns model multi-department governance.',status('work','Working demo')]
  ];
  view.innerHTML=
    '<div class="card section"><h2>Portfolio evidence</h2><p>This application is designed to show how AJ approaches the actual workflow: inspect evidence, explain the finding, prioritize the work, support the content owner, document the change, and measure the result.</p><p><a href="https://aj-kivela-portfolio.lovable.app/" target="_blank" rel="noopener">AJ Kivela Portfolio</a> · <a href="https://github.com/ajkivela369-coder/servicebridge-advocate" target="_blank" rel="noopener">ServiceBridge Advocate GitHub</a></p></div>'+
    '<table><tr><th>Role requirement</th><th>Evidence in SearchSignal</th><th>Status</th></tr>'+
    rows.map((r)=>'<tr><td><b>'+r[0]+'</b></td><td>'+r[1]+'</td><td>'+r[2]+'</td></tr>').join('')+
    '</table>'+
    '<div class="callout section" style="margin-top:16px"><b>Accuracy boundary:</b> SearchSignal demonstrates real auditing logic, structured-data generation, prioritization, support workflows and technical concepts. It does not present unconnected Search Console, Analytics, WordPress, Apache, PHP or MariaDB systems as production experience.</div>';
}

show('dashboard');