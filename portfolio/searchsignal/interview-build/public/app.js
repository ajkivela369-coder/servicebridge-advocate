const state={lastAudit:null,lastSiteScan:null,caseStudyUrl:'https://geiselmed.dartmouth.edu/',changeLab:null,scaleRun:null};

const pages=[
  ['dashboard','Dashboard'],
  ['interview','Geisel Interview Mode'],
  ['auditor','Live URL Auditor'],
  ['changelab','Change Lab'],
  ['site','Site Intelligence'],
  ['patterns','Site Patterns'],
  ['documents','Document Intelligence'],
  ['optimizer','Content Optimizer'],
  ['schema','Structured Data Studio'],
  ['roadmap','Priority Roadmap'],
  ['reporting','Progress & Reporting'],
  ['analytics','Analytics & AI Visibility'],
  ['scale','20K Scale Simulator'],
  ['wordpress','WordPress Support'],
  ['training','Training Center'],
  ['lab','Technical Lab'],
  ['coverage','Requirements Coverage']
];

const nav=document.getElementById('nav');
const view=document.getElementById('view');
const navIcons={
  dashboard:'nav-dashboard.svg',interview:'nav-interview.svg',auditor:'nav-auditor.svg',changelab:'nav-lab.svg',site:'nav-roadmap.svg',patterns:'nav-roadmap.svg',documents:'nav-schema.svg',
  optimizer:'nav-optimizer.svg',schema:'nav-schema.svg',roadmap:'nav-roadmap.svg',reporting:'nav-analytics.svg',
  analytics:'nav-analytics.svg',scale:'nav-lab.svg',wordpress:'nav-wordpress.svg',training:'nav-training.svg',
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
  const routes={dashboard,interview,auditor,changelab:changeLab,site:siteIntelligence,patterns:sitePatterns,documents:documentIntelligence,optimizer,schemaStudio,roadmap,reporting:progressReporting,analytics:analyticsV2,scale:scaleSimulator,wordpress:wordpressV2,training,lab,coverage:coverageV2};
  (routes[id]||dashboard)();
  window.scrollTo(0,0);
  if(location.hash!=='#'+id) history.replaceState(null,'','#'+id);
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
  const geiselMetaDraft="Explore MD education, health sciences master's programs, research, news, events, centers, and affiliated hospitals at Geisel School of Medicine at Dartmouth.";
  const geiselSchemaDraft={"@context":"https://schema.org","@type":"WebPage","name":"Geisel School of Medicine at Dartmouth","url":"https://geiselmed.dartmouth.edu/","isPartOf":{"@type":"WebSite","name":"Geisel School of Medicine at Dartmouth","url":"https://geiselmed.dartmouth.edu/"}};
  view.innerHTML=
    '<div class="card section"><div class="eyebrow">INTERVIEW CASE STUDY</div><h2>How I would approach Geisel\'s web-visibility work</h2><p>Start with observable evidence, rank the work transparently, make safe changes, help content owners, then measure whether the change helped.</p><div class="header-actions"><button id="startCaseAudit" class="primary">Run live public-page audit</button><button data-go="site" class="secondary">Run bounded site scan</button><button data-go="roadmap" class="secondary">Open prioritization engine</button></div><p class="muted mini">Work-in-progress independent portfolio prototype. Public data only; no Dartmouth credentials, analytics access, or production administration is implied.</p></div>'+
    '<div class="card section"><div class="eyebrow">PUBLIC GEISEL SNAPSHOT · OCT 1, 2026</div><h2>What SearchSignal already found</h2><p class="muted">A fresh public homepage audit plus a bounded six-page same-origin sample. These are observable web signals, not claims about Geisel\'s internal priorities.</p><div class="grid three" style="margin-top:14px"><div><div class="metric">80</div><b>SEO rubric</b><p class="muted mini">Homepage snapshot</p></div><div><div class="metric">41</div><b>GEO readiness</b><p class="muted mini">Homepage snapshot</p></div><div><div class="metric">0</div><b>Fetch errors</b><p class="muted mini">6-page sample</p></div></div><div class="table-wrap" style="margin-top:14px"><table><tr><th>Observed signal</th><th>Public evidence</th><th>Practical next move</th></tr><tr><td><b>Missing meta description</b></td><td>Homepage audit did not detect one.</td><td>Write a specific plain-language summary for search snippets.</td></tr><tr><td><b>No JSON-LD detected</b></td><td>No schema types detected on the homepage.</td><td>Add truthful schema.org markup that matches visible content.</td></tr><tr><td><b>Placeholder / empty links</b></td><td>14 targets flagged on the homepage.</td><td>Review whether they are intentional controls; replace broken or placeholder hrefs.</td></tr><tr><td><b>Site-sample consistency</b></td><td>3/6 pages missing descriptions; 2/6 missing canonicals; 1/6 with an H1 issue.</td><td>Turn these into a prioritized, owner-aware cleanup queue.</td></tr></table></div><div class="callout" style="margin-top:14px"><b>The point:</b> the app turns a vague “improve web visibility” assignment into evidence, a ranked work queue, safe implementation boundaries, editor support, and measurable follow-up.</div></div>'+
    '<div class="card section"><div class="eyebrow">READY-TO-REVIEW REMEDIATION</div><h2>Geisel homepage fix pack</h2><p>This does not publish anything to Dartmouth. It converts two verified public findings into implementation-ready drafts and turns the 14 link flags into a human-review task.</p><div class="grid two"><div><h3>Meta description draft</h3><div class="callout">'+esc(geiselMetaDraft)+'</div><p><button id="copyGeiselMeta" class="secondary">Copy meta description</button></p><p class="muted mini">Drafted only from information visible on the public homepage; editorial approval still required.</p></div><div><h3>Minimal WebPage JSON-LD draft</h3><pre>'+esc(JSON.stringify(geiselSchemaDraft,null,2))+'</pre><p><button id="copyGeiselSchema" class="secondary">Copy JSON-LD</button> <button data-go="schema" class="secondary">Open schema studio</button></p></div></div><div class="callout warn" style="margin-top:14px"><b>Link-review task:</b> SearchSignal flagged 14 empty/placeholder href targets. Some may be intentional JavaScript controls, so they should be inspected in context before any change. The fix is not “delete 14 links”; it is “review 14 flagged targets and repair only the unintended ones.”</div><div class="header-actions" style="margin-top:14px"><button id="downloadGeiselFixPack" class="primary">Download fix pack</button><span class="muted mini">Includes evidence, drafts, and review notes.</span></div></div>'+
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
  const copyText=async(id,textValue)=>{
    await navigator.clipboard.writeText(textValue);
    const button=document.getElementById(id);
    const prior=button.textContent;
    button.textContent='Copied';
    setTimeout(()=>button.textContent=prior,1200);
  };
  document.getElementById('copyGeiselMeta').onclick=()=>copyText('copyGeiselMeta',geiselMetaDraft);
  document.getElementById('copyGeiselSchema').onclick=()=>copyText('copyGeiselSchema',JSON.stringify(geiselSchemaDraft,null,2));
  document.getElementById('downloadGeiselFixPack').onclick=()=>{
    const pack={
      generated:'2026-10-01',
      target:'https://geiselmed.dartmouth.edu/',
      boundary:'Independent public-data portfolio draft. Review and approval required before any production change.',
      observed:{seo:80,geo:41,homepageFindings:['Missing meta description','No JSON-LD detected','14 empty/placeholder href targets flagged for contextual review'],siteSample:{pages:6,fetchErrors:0,missingDescriptions:3,missingCanonicals:2,h1Issues:1}},
      proposed:{metaDescription:geiselMetaDraft,jsonLd:geiselSchemaDraft,linkReview:'Inspect the 14 flagged href targets in context; repair only unintended empty/placeholder links.'}
    };
    const blob=new Blob([JSON.stringify(pack,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='geisel-homepage-fix-pack-2026-10-01.json';a.click();URL.revokeObjectURL(url);
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
  return list.map((c)=>'<div class="check"><span class="'+(c.ok?'ok':'bad')+'">'+(c.ok?'✓':'×')+'</span><span>'+esc(c.name)+'</span><span>'+(c.ok?'pass':'review')+'</span></div>').join('');
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
      '<div style="margin-top:12px" class="header-actions"><button class="secondary" id="copyAudit">Copy plain-language summary</button><button class="secondary" id="explainEditor">Explain to department editor</button><button class="secondary" id="exportAuditJson">Export JSON</button><button class="secondary" id="exportAuditCsv">Export CSV</button></div>'+
    '</div>';
  document.getElementById('copyAudit').onclick=function(){
    navigator.clipboard.writeText(auditSummary(d));
    this.textContent='Copied';
  };
  document.getElementById('explainEditor').onclick=function(){
    const top=d.findings.slice(0,5).map((f)=>'• '+f.label+': '+f.fix).join('\n');
    const note='Here are the page changes I would review with the content owner. Nothing is published automatically.\n\n'+top+'\n\nAccessibility notes are heuristic signals only and still require human testing.';
    navigator.clipboard.writeText(note);
    this.textContent='Editor explanation copied';
  };
  document.getElementById('exportAuditJson').onclick=()=>downloadFile('searchsignal-audit.json',JSON.stringify(d,null,2),'application/json');
  document.getElementById('exportAuditCsv').onclick=()=>{
    const rows=[['severity','finding','evidence','recommendation']].concat(d.findings.map((x)=>[x.severity,x.label,x.evidence,x.fix]));
    downloadFile('searchsignal-audit.csv',rows.map((r)=>r.map(csvCell).join(',')).join('\n'),'text/csv');
  };
}

function auditSummary(d){
  return 'SearchSignal audit: '+d.finalUrl+'\nSEO '+d.scores.seo+'/100 · GEO '+d.scores.geo+'/100\n'+d.findings.map((f)=>f.severity+': '+f.label+' — '+f.fix).join('\n');
}

function siteIntelligence(){
  setTitle('Site Intelligence','Run a bounded same-site crawl, inventory linked documents, and validate redirect chains.');
  view.innerHTML=
    '<div class="grid two section">'+
      '<div class="card"><h2>Bounded site scan</h2><p class="muted">Crawls public HTML on the same origin only. Query strings are removed to reduce duplicate/infinite crawl paths; the demo is capped at 12 pages and supports a polite delay between requests.</p><div class="form-row"><input id="siteUrl" value="'+esc(state.caseStudyUrl)+'" aria-label="Starting URL"><select id="siteLimit" style="max-width:120px" aria-label="Page limit"><option>4</option><option selected>6</option><option>8</option><option>10</option><option>12</option></select><select id="crawlDelay" style="max-width:150px" aria-label="Delay between page requests"><option value="0">No delay</option><option value="150" selected>150 ms delay</option><option value="300">300 ms delay</option><option value="500">500 ms delay</option></select><button id="siteScanBtn" class="primary">Scan site</button></div></div>'+
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
    const response=await fetch('/api/site-scan',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({url:document.getElementById('siteUrl').value,limit:Number(document.getElementById('siteLimit').value),delayMs:Number(document.getElementById('crawlDelay').value)})});
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
      '<div class="card" id="optOut"><h2>AI answer readiness preview</h2><p class="muted">Recommendations are produced by the private server-side workflow and returned as editable drafts.</p></div>'+
    '</div>';
  document.getElementById('optBtn').onclick=async()=>{
    const button=document.getElementById('optBtn');
    button.disabled=true; button.textContent='Generating…';
    try{
      const response=await fetch('/api/recommendations',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({text:document.getElementById('copy').value.trim()})});
      const data=await response.json();
      if(!response.ok) throw new Error(data.error||'Recommendation generation failed');
      document.getElementById('optOut').innerHTML=
        '<h2>Editable draft</h2>'+
        '<p><b>Answer-first opening:</b> '+esc(data.opening||'Add a concise opening that directly states the page purpose.')+'</p>'+
        '<p><b>Suggested outline:</b> '+data.outline.map(esc).join(' → ')+'</p>'+
        '<p><b>GEO additions:</b> '+data.geo.map(esc).join(', ')+'.</p>'+
        '<p><b>SEO additions:</b> '+data.seo.map(esc).join(', ')+'.</p>'+
        '<div class="callout">'+esc(data.boundary)+'</div>';
    }catch(error){
      document.getElementById('optOut').innerHTML='<h2>Recommendation error</h2><p>'+esc(error.message)+'</p>';
    }finally{
      button.disabled=false; button.textContent='Generate draft recommendations';
    }
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
  const cell=(a,i,f)=>'<input class="prio-input" type="number" min="1" max="5" value="'+a[f]+'" data-i="'+i+'" data-f="'+f+'" aria-label="'+f+' for '+esc(a.area)+'">';
  let lastRanked=[];
  view.innerHTML=
    '<div class="callout section"><b>Protected prioritization model:</b> the public interface exposes the decision factors and resulting rank, while the weighting logic stays server-side. Every input remains editable so assumptions can still be challenged.</div>'+
    '<div class="card section"><h2>Interview scenario inputs</h2><p class="muted">These starting values are illustrative—not Geisel internal data. In practice I would replace them with stakeholder priorities, Search Console/Analytics evidence, service demand, and available staff capacity.</p></div>'+
    '<div class="table-wrap"><table><thead><tr><th>Area</th><th>Work</th>'+factors.map((f)=>'<th>'+f[1]+'<div class="muted mini">1–5</div></th>').join('')+'<th>Phase</th><th>Score</th></tr></thead><tbody id="roadmapRows"></tbody></table></div>'+
    '<div class="section" style="margin-top:12px"><button class="secondary" id="copyRoadmap">Copy ranked roadmap</button> <button class="secondary" data-go="interview">Back to interview mode</button></div>';
  const render=async()=>{
    const tbody=document.getElementById('roadmapRows');
    tbody.innerHTML='<tr><td colspan="'+(factors.length+4)+'">Calculating priorities…</td></tr>';
    try{
      const response=await fetch('/api/prioritize',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({items:areas})});
      const data=await response.json();
      if(!response.ok) throw new Error(data.error||'Prioritization failed');
      lastRanked=data.ranked.map((r)=>({a:areas[r.index],i:r.index,s:r.score,phase:r.phase}));
      tbody.innerHTML=lastRanked.map(({a,i,s,phase})=>
        '<tr><td><b>'+esc(a.area)+'</b></td><td>'+esc(a.work)+'</td>'+
        factors.map((f)=>'<td>'+cell(a,i,f[0])+'</td>').join('')+
        '<td><span class="phase '+phase.toLowerCase()+'">'+phase+'</span></td><td><b>'+Number(s).toFixed(1)+'</b></td></tr>'
      ).join('');
      document.querySelectorAll('.prio-input').forEach((input)=>{
        input.onchange=()=>{
          const i=Number(input.dataset.i);
          const f=input.dataset.f;
          areas[i][f]=Math.max(1,Math.min(5,Number(input.value)||1));
          render();
        };
      });
    }catch(error){
      tbody.innerHTML='<tr><td colspan="'+(factors.length+4)+'"><span class="bad">'+esc(error.message)+'</span></td></tr>';
    }
  };
  render();
  document.getElementById('copyRoadmap').onclick=function(){
    const text=['SearchSignal priority roadmap — illustrative inputs']
      .concat(lastRanked.map((x,n)=>(n+1)+'. '+x.a.area+' — '+x.a.work+' — '+x.phase+' — '+Number(x.s).toFixed(1)))
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
    ['Prioritized phased roadmap','Editable decision factors with server-side proprietary ranking logic and Now / Next / Later planning.',status('work','Working')],
    ['Search Console / Analytics','Browser-local CSV import is working; authenticated account connections remain intentionally unconnected.',status('work','CSV workflow')],
    ['WordPress support','Ticket workflow, page-level support model, safe change boundary and escalation logic.',status('work','Working demo')],
    ['WordPress admin integration','Prepared as an authenticated connector path; not represented as live.',status('ready','Connector-ready')],
    ['WordPress Multisite lab','Local Apache/PHP/MariaDB acceptance artifacts document hands-on Multisite practice without presenting it as production employment.',status('lab','Validated lab')],
    ['Training & documentation','Eight mini training modules with plain-language guidance and escalation rules.',status('work','Working')],
    ['Apache / PHP / MariaDB literacy','Interactive learning lab demonstrates concepts and safe escalation boundary.',status('lab','Learning lab')],
    ['Large decentralized environment','Dashboard + roadmap + ownership/status patterns model multi-department governance.',status('work','Working demo')]
  ];
  view.innerHTML=
    '<div class="card section"><h2>Portfolio evidence</h2><p>This application is designed to show how AJ approaches the actual workflow: inspect evidence, explain the finding, prioritize the work, support the content owner, document the change, and measure the result.</p><p><a href="https://aj-kivela-portfolio.lovable.app/" target="_blank" rel="noopener">AJ Kivela Portfolio</a></p><p class="muted mini">Source code is private. Selected implementation details can be reviewed by screen share during an interview.</p></div>'+
    '<table><tr><th>Role requirement</th><th>Evidence in SearchSignal</th><th>Status</th></tr>'+
    rows.map((r)=>'<tr><td><b>'+r[0]+'</b></td><td>'+r[1]+'</td><td>'+r[2]+'</td></tr>').join('')+
    '</table>'+
    '<div class="callout section" style="margin-top:16px"><b>Accuracy boundary:</b> SearchSignal demonstrates real auditing logic, structured-data generation, prioritization, support workflows and technical concepts. It does not present unconnected Search Console, Analytics, WordPress, Apache, PHP or MariaDB systems as production experience.</div>';
}


function downloadFile(name,content,type='text/plain'){
  const blob=new Blob([content],{type});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),0);
}
function csvCell(value){
  const s=String(value??'');
  return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;
}
function safeDate(value){
  const d=new Date(value);
  return Number.isNaN(d.getTime())?null:d;
}
function filenameFromUrl(raw){
  try{return decodeURIComponent(new URL(raw).pathname.split('/').filter(Boolean).pop()||'document');}
  catch{return raw;}
}
function changeLab(){
  setTitle('Change Lab','Practice the full find → fix → verify loop on a synthetic sandbox page.');
  view.innerHTML=
    '<div class="callout section"><b>Safety boundary:</b> No production site modified. Every change below applies only to a synthetic sandbox copy.</div>'+
    '<div class="grid two section">'+
      '<div class="card"><div class="eyebrow">SANDBOX PAGE</div><h2>Synthetic Health Sciences Program page</h2><p class="muted">Use this page to demonstrate implementation mechanics without touching Dartmouth or any external CMS.</p><div class="header-actions"><button id="labAnalyze" class="secondary">1 · Detect issues</button><button id="labPrepare" class="secondary">2 · Prepare fix</button><button id="labApply" class="primary">3 · Apply to sandbox</button><button id="labVerify" class="secondary">4 · Verify</button><button id="labReset" class="secondary">Reset</button></div></div>'+
      '<div class="card"><h2>Workflow state</h2><div id="labState">'+status('ready','Ready')+'<p class="muted">Start with issue detection.</p></div></div>'+
    '</div>'+
    '<div id="changeLabOut"></div>';
  const run=async(action)=>{
    const out=document.getElementById('changeLabOut');
    document.querySelectorAll('#labAnalyze,#labPrepare,#labApply,#labVerify,#labReset').forEach((b)=>b.disabled=true);
    out.innerHTML='<div class="card">Running '+esc(action)+' in the sandbox…</div>';
    try{
      const r=await fetch('/api/change-lab',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action})});
      const d=await r.json();
      if(!r.ok) throw new Error(d.error||'Change Lab failed');
      state.changeLab=d;
      renderChangeLab(d);
    }catch(error){out.innerHTML='<div class="card"><h2>Change Lab error</h2><p>'+esc(error.message)+'</p></div>';}
    finally{document.querySelectorAll('#labAnalyze,#labPrepare,#labApply,#labVerify,#labReset').forEach((b)=>b.disabled=false);}
  };
  document.getElementById('labAnalyze').onclick=()=>run('analyze');
  document.getElementById('labPrepare').onclick=()=>run('prepare');
  document.getElementById('labApply').onclick=()=>run('apply');
  document.getElementById('labVerify').onclick=()=>run('verify');
  document.getElementById('labReset').onclick=()=>run('reset');
  run('analyze');
}
function renderChangeLab(d){
  const issueRows=d.issues.map((x)=>'<tr><td><span class="sev '+x.severity+'">'+x.severity+'</span></td><td><b>'+esc(x.label)+'</b><div class="muted mini">'+esc(x.evidence)+'</div></td></tr>').join('');
  const changeRows=d.changes.map((x)=>'<tr><td><b>'+esc(x.field)+'</b></td><td><code>'+esc(x.before)+'</code></td><td><code>'+esc(x.after)+'</code></td></tr>').join('');
  const validation=d.validation?'<div class="grid three">'+
    kpi('H1 count',d.validation.h1Count,'target: 1')+
    kpi('Schema',d.validation.schemaTypes.join(', ')||'None','sandbox JSON-LD')+
    kpi('Descriptive links',d.validation.descriptiveInternalLinks,d.validation.placeholderLinks+' placeholder')+
    '</div><div class="callout" style="margin-top:12px"><b>Validation:</b> meta description '+d.validation.metaLength+' chars · '+esc(d.validation.htmlStatus)+'.</div>':'<div class="callout warn">Apply the prepared fix to the sandbox before validation results are shown.</div>';
  const reAudit=d.reAudit?'<div class="card section"><div class="eyebrow">RE-AUDIT RESULT</div><h2>Before → after</h2><div class="grid two"><div>'+kpi('SEO',d.reAudit.before.seo+' → '+d.reAudit.after.seo,'synthetic sandbox rubric')+'</div><div>'+kpi('GEO',d.reAudit.before.geo+' → '+d.reAudit.after.geo,'synthetic sandbox rubric')+'</div></div><p class="muted"><b>Still requires:</b> '+d.reAudit.remaining.map(esc).join(' · ')+'</p></div>':'';
  document.getElementById('labState').innerHTML=status(d.reAudit?'work':d.validation?'work':'ready',d.reAudit?'Verified':d.validation?'Sandbox changed':'Prepared / detected')+'<p class="muted mini">'+esc(d.boundary)+'</p>';
  document.getElementById('changeLabOut').innerHTML=
    '<div class="grid two section"><div class="card"><h2>Detected issues</h2><table><tr><th>Priority</th><th>Evidence</th></tr>'+issueRows+'</table></div>'+
    '<div class="card"><h2>Sandbox source</h2><div class="diff-labels"><span>Current / applied copy</span><span>'+esc(d.action)+'</span></div><pre>'+esc(d.appliedHtml)+'</pre></div></div>'+
    '<div class="card section"><h2>Before / after implementation diff</h2><div class="table-wrap"><table><tr><th>Change</th><th>Before</th><th>After</th></tr>'+changeRows+'</table></div></div>'+
    '<div class="card section"><h2>Validation</h2>'+validation+'</div>'+reAudit+
    '<div class="callout section"><b>No production site modified.</b> This workflow is intentionally synthetic so the implementation steps can be inspected safely.</div>';
}

function sitePatterns(){
  setTitle('Site Patterns','Turn page-by-page findings into repeatable site-level cleanup patterns.');
  const scan=state.lastSiteScan;
  const pages=(scan?.pages||[]).filter((p)=>!p.error);
  const titleGroups={};
  const canonicalGroups={};
  pages.forEach((p)=>{
    const title=(p.title||'(missing)').trim().toLowerCase();
    titleGroups[title]=(titleGroups[title]||[]).concat(p.url);
    const canonical=(p.canonical||'(missing)').trim().toLowerCase();
    canonicalGroups[canonical]=(canonicalGroups[canonical]||[]).concat(p.url);
  });
  const duplicateTitles=Object.entries(titleGroups).filter(([k,v])=>k!=='(missing)'&&v.length>1);
  const duplicateCanonicals=Object.entries(canonicalGroups).filter(([k,v])=>k!=='(missing)'&&v.length>1);
  const brokenDocs=(scan?.documents||[]).filter((d)=>d.error||Number(d.status)>=400);
  const actual=scan?[
    ['Duplicate title clusters',duplicateTitles.length,'titles repeated within this bounded crawl'],
    ['Missing canonicals',scan.summary.missingCanonicals,'sampled pages'],
    ['H1 structure issues',scan.summary.h1Issues,'sampled pages'],
    ['Broken document links',brokenDocs.length,'checked linked documents'],
    ['Duplicate canonical clusters',duplicateCanonicals.length,'same canonical used by multiple sampled URLs']
  ]:[
    ['Duplicate title clusters','—','Run a bounded site scan first'],
    ['Missing canonicals','—','Run a bounded site scan first'],
    ['H1 structure issues','—','Run a bounded site scan first'],
    ['Broken document links','—','Run a bounded site scan first'],
    ['Duplicate canonical clusters','—','Run a bounded site scan first']
  ];
  view.innerHTML=
    '<div class="grid two section"><div class="card"><div class="eyebrow">OBSERVED SAMPLE</div><h2>Pattern summary</h2><p class="muted">'+(scan?'Derived from the last bounded crawl. Counts apply only to that sample.':'No bounded crawl is loaded yet. Run Site Intelligence to replace placeholders with observed sample data.')+'</p><table><tr><th>Pattern</th><th>Count</th><th>Scope</th></tr>'+actual.map((x)=>'<tr><td><b>'+x[0]+'</b></td><td>'+x[1]+'</td><td>'+x[2]+'</td></tr>').join('')+'</table><p style="margin-top:12px"><button class="secondary" data-go="site">Run / refresh bounded scan</button></p></div>'+
    '<div class="card"><div class="eyebrow">SITE CONTROL FILES</div><h2>robots.txt + sitemap.xml</h2><p class="muted">Check only public control files. This does not imply Search Console or server access.</p><button id="metaCheckBtn" class="secondary">Inspect public control files</button><div id="metaCheckOut" class="muted mini" style="margin-top:12px">Not checked yet.</div></div></div>'+
    '<div class="card section"><h2>Pattern clusters</h2>'+
      (duplicateTitles.length?'<h3>Repeated titles</h3>'+duplicateTitles.map(([t,urls])=>'<div class="pattern-row"><b>'+esc(t)+'</b><span>'+urls.length+' pages</span><div class="muted mini">'+urls.map(esc).join('<br>')+'</div></div>').join(''):'<p class="muted">No duplicate title cluster detected in the loaded sample.</p>')+
      (duplicateCanonicals.length?'<h3 style="margin-top:16px">Canonical clusters</h3>'+duplicateCanonicals.map(([u,urls])=>'<div class="pattern-row"><b>'+esc(u)+'</b><span>'+urls.length+' pages point here</span></div>').join(''):'')+
    '</div>'+
    '<div class="callout section"><b>Scale boundary:</b> a bounded crawl can expose patterns but cannot prove site-wide counts. Use the 20K Scale Simulator for a clearly labeled synthetic workload model.</div>';
  document.getElementById('metaCheckBtn').onclick=async function(){
    const out=document.getElementById('metaCheckOut');this.disabled=true;this.textContent='Checking…';
    try{
      const r=await fetch('/api/site-meta',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({url:scan?.startUrl||state.caseStudyUrl})});
      const d=await r.json();if(!r.ok) throw new Error(d.error||'Check failed');
      out.innerHTML='<div class="check"><span class="'+(d.robots.status===200?'ok':'bad')+'">'+(d.robots.status||'—')+'</span><span>robots.txt</span><span>'+esc(d.robots.contentType||d.robots.error||'')+'</span></div>'+
        '<div class="check"><span class="'+(d.sitemap.status===200?'ok':'bad')+'">'+(d.sitemap.status||'—')+'</span><span>sitemap.xml</span><span>'+esc(d.sitemap.contentType||d.sitemap.error||'')+'</span></div>';
    }catch(error){out.textContent=error.message;}
    finally{this.disabled=false;this.textContent='Inspect public control files';}
  };
}

function documentIntelligence(){
  setTitle('Document Intelligence','Treat PDF and Office files as governed web content, not invisible attachments.');
  const scan=state.lastSiteScan;
  const docs=scan?.documents||[];
  const names={};
  docs.forEach((d)=>{const n=filenameFromUrl(d.url).toLowerCase();names[n]=(names[n]||0)+1;});
  const rows=docs.map((d)=>{
    const lm=safeDate(d.lastModified);
    const ageDays=lm?Math.floor((Date.now()-lm.getTime())/86400000):null;
    const signals=[];
    if(d.error||Number(d.status)>=400) signals.push('Broken / unavailable');
    if(d.bytes&&d.bytes>5*1024*1024) signals.push('Oversized >5 MB');
    if(names[filenameFromUrl(d.url).toLowerCase()]>1) signals.push('Duplicate filename');
    if(ageDays!==null&&ageDays>730) signals.push('Old Last-Modified signal');
    if(!d.linkText||/^(download|click here|here)$/i.test(d.linkText)) signals.push('Weak link text');
    return '<tr><td><b>'+esc(filenameFromUrl(d.url))+'</b><div class="muted mini">'+esc(d.url)+'</div></td><td>'+(d.error?'Error':d.status||'—')+'</td><td>'+(d.bytes?Math.round(d.bytes/1024)+' KB':'Unknown')+'</td><td>'+esc(d.lastModified||'Unknown')+'</td><td>'+esc((d.sources||[d.source]).filter(Boolean).length)+'</td><td>'+(signals.length?signals.map((s)=>'<span class="doc-signal">'+esc(s)+'</span>').join(' '):'<span class="status work">No HTTP-level flag</span>')+'</td></tr>';
  }).join('');
  view.innerHTML=
    '<div class="callout section"><b>Accessibility boundary:</b> HTTP metadata, filenames, and link context can flag review needs, but they cannot determine whether a PDF or Office file is accessible. Document-level accessibility still requires appropriate inspection/testing.</div>'+
    '<div class="grid three section">'+
      kpi('Discovered',docs.length,scan?'last bounded crawl':'run Site Intelligence')+
      kpi('Broken',docs.filter((d)=>d.error||Number(d.status)>=400).length,'HTTP / fetch signal')+
      kpi('Large files',docs.filter((d)=>d.bytes>5*1024*1024).length,'>5 MB review threshold')+
    '</div>'+
    '<div class="card section"><h2>Document inventory</h2>'+(rows?'<div class="table-wrap"><table><tr><th>Document</th><th>Status</th><th>Size</th><th>Last-Modified</th><th>Referencing pages</th><th>Review signals</th></tr>'+rows+'</table></div>':'<p class="muted">No document inventory loaded. Run a bounded site scan to discover public PDF/Office links.</p>')+'</div>'+
    '<div class="grid two"><div class="card"><h2>What a crawl can support</h2><p>Broken document links, HTTP metadata, file size, duplicate filenames in the discovered sample, weak link text, and which crawled pages reference a document.</p></div><div class="card"><h2>What needs broader inventory or human review</h2><p>True orphan detection, document accessibility conformance, content accuracy, retention requirements, and whether an old file should be retired.</p></div></div>';
}

function wordpressV2(){
  setTitle('WordPress Support Center','Walk a support request from user language to diagnosis, safe steps, escalation, and reusable training.');
  const scenarios={
    nav:{title:'My page disappeared from navigation',user:'“The page is still published, but nobody can find it in the menu.”',diagnosis:'Confirm the page URL/status first, then inspect the assigned menu/navigation block and parent-child structure. Avoid changing theme code for a content-level navigation issue.',steps:['Confirm the page is published and the expected URL resolves.','Check whether the correct menu/navigation block includes the page.','Verify parent/child placement and label text.','Preview the navigation at desktop and mobile widths.','Document the change and owner.'],escalation:'Escalate if the menu is generated by theme/application logic, permissions block the editor, or the issue appears across many sites.',reply:'I found that the page itself is still available. I would next check the menu/navigation assignment and page placement before touching any theme or server code.',kb:'KB: Restore a published page to site navigation — verify page status → menu assignment → hierarchy → responsive preview → document the change.'},
    redirect:{title:'I need to redirect an old page',user:'“We renamed a program page and want the old link to go to the new one.”',diagnosis:'Verify whether the move is permanent, confirm the target is the correct canonical destination, check for loops/chains, and use the approved redirect layer for the site.',steps:['Confirm old and new URLs with the content owner.','Verify the destination returns 200 and is the intended canonical page.','Check whether a redirect already exists.','Use a 301 for a confirmed permanent move.','Validate the full chain and update important internal links.'],escalation:'Escalate if the redirect requires Apache/server configuration, creates a loop, conflicts with multisite routing, or affects a large URL family.',reply:'I can prepare the redirect after confirming the new URL is the permanent destination. I would also validate the chain and update important internal links so users and crawlers do not rely on an avoidable hop.',kb:'KB: Permanent page moves — confirm ownership → destination → existing rules → 301 → validate chain → update internal links.'},
    program:{title:'How should I structure a program page for search / AI answers?',user:'“We have good information, but the page is hard to scan and does not answer common questions quickly.”',diagnosis:'Keep the factual content, then improve information hierarchy, answer-first sections, descriptive headings, source context, internal links, and truthful structured data where appropriate.',steps:['State the program purpose clearly near the top.','Use one H1 and descriptive H2/H3 sections.','Add concise answers for admissions, curriculum, outcomes, cost/support, and contacts where accurate.','Use descriptive internal links to authoritative supporting pages.','Add only structured data that matches visible content.'],escalation:'Escalate claims, policy-sensitive content, schema that requires institutional review, or template changes affecting many sites.',reply:'I would keep the program facts intact and reorganize them so students can answer key questions quickly. The goal is clearer information architecture first; search and AI visibility should follow from that clarity.',kb:'KB: Program-page structure — purpose → key facts → requirements → curriculum → support → outcomes → contacts/sources.'}
  };
  view.innerHTML=
    '<div class="grid two section"><div class="card"><h2>Choose a support scenario</h2><div class="support-choices">'+
      Object.entries(scenarios).map(([k,s],i)=>'<button class="'+(i===0?'primary':'secondary')+'" data-support="'+k+'">'+esc(s.title)+'</button>').join('')+
      '</div><div class="callout warn" style="margin-top:14px"><b>Boundary:</b> this is a support simulation. No live WordPress admin connection is represented.</div></div>'+
      '<div class="card"><h2>Safe change boundary</h2><p><b>Handle directly:</b> page editing, content structure, links, media, alt text, approved redirects, metadata, documentation and training.</p><p><b>Escalate:</b> server config, Apache routing, authentication, multisite architecture, risky PHP/theme code, or changes with broad blast radius.</p></div></div>'+
    '<div id="supportWorkflow"></div>';
  const render=(key)=>{
    const s=scenarios[key];
    document.querySelectorAll('[data-support]').forEach((b)=>{b.className=b.dataset.support===key?'primary':'secondary';});
    document.getElementById('supportWorkflow').innerHTML=
      '<div class="card section"><div class="eyebrow">USER ISSUE</div><h2>'+esc(s.title)+'</h2><p>'+esc(s.user)+'</p></div>'+
      '<div class="workflow-rail section">'+
        '<div class="card"><div class="stepnum">01</div><h3>Diagnosis</h3><p>'+esc(s.diagnosis)+'</p></div>'+
        '<div class="card"><div class="stepnum">02</div><h3>Editor-safe steps</h3><ol>'+s.steps.map((x)=>'<li>'+esc(x)+'</li>').join('')+'</ol></div>'+
        '<div class="card"><div class="stepnum">03</div><h3>Escalation decision</h3><p>'+esc(s.escalation)+'</p></div>'+
        '<div class="card"><div class="stepnum">04</div><h3>Plain-language response</h3><p>'+esc(s.reply)+'</p><button id="copySupportReply" class="secondary">Copy response</button></div>'+
        '<div class="card"><div class="stepnum">05</div><h3>Knowledge-base article</h3><p>'+esc(s.kb)+'</p><button id="copySupportKb" class="secondary">Copy KB draft</button></div>'+
      '</div>';
    document.getElementById('copySupportReply').onclick=()=>navigator.clipboard.writeText(s.reply);
    document.getElementById('copySupportKb').onclick=()=>navigator.clipboard.writeText(s.kb);
  };
  document.querySelectorAll('[data-support]').forEach((b)=>b.onclick=()=>render(b.dataset.support));
  render('nav');
}

function parseCsvLine(line){
  const out=[];let cur='';let quoted=false;
  for(let i=0;i<line.length;i++){
    const ch=line[i];
    if(ch==='"'&&quoted&&line[i+1]==='"'){cur+='"';i++;continue;}
    if(ch==='"'){quoted=!quoted;continue;}
    if(ch===','&&!quoted){out.push(cur);cur='';continue;}
    cur+=ch;
  }
  out.push(cur);return out;
}
function parseCsv(text){
  const lines=text.split(/\r?\n/).filter((x)=>x.trim());
  if(lines.length<2) throw new Error('CSV needs a header row and at least one data row.');
  const headers=parseCsvLine(lines[0]).map((x)=>x.trim());
  return lines.slice(1).map((line)=>{
    const values=parseCsvLine(line);const row={};
    headers.forEach((h,i)=>row[h]=values[i]??'');return row;
  });
}
function findHeader(row,candidates){
  const keys=Object.keys(row);
  const lower=keys.map((k)=>k.toLowerCase().replace(/[\s_-]+/g,''));
  for(const candidate of candidates){
    const i=lower.indexOf(candidate.toLowerCase().replace(/[\s_-]+/g,''));
    if(i>=0) return keys[i];
  }
  return null;
}
function summarizeCsvRows(rows,changeDate){
  if(!rows.length) throw new Error('No rows found.');
  const dateKey=findHeader(rows[0],['date','day']);
  if(!dateKey) throw new Error('A Date column is required for 7/30/90-day comparison.');
  const clicksKey=findHeader(rows[0],['clicks']);
  const impressionsKey=findHeader(rows[0],['impressions']);
  const sessionsKey=findHeader(rows[0],['sessions','organicsessions','users']);
  const positionKey=findHeader(rows[0],['position','averageposition']);
  const pageKey=findHeader(rows[0],['page','landingpage','url']);
  const parsed=rows.map((r)=>({...r,__date:safeDate(r[dateKey])})).filter((r)=>r.__date).sort((a,b)=>a.__date-b.__date);
  if(!parsed.length) throw new Error('No valid dates found.');
  const change=safeDate(changeDate)||parsed[Math.floor(parsed.length/2)].__date;
  const sum=(arr,key)=>key?arr.reduce((n,r)=>n+(Number(String(r[key]).replace(/[%,$]/g,''))||0),0):null;
  const avg=(arr,key)=>key&&arr.length?arr.reduce((n,r)=>n+(Number(String(r[key]).replace(/[%,$]/g,''))||0),0)/arr.length:null;
  const result={changeDate:change.toISOString().slice(0,10),windows:[],affectedPages:pageKey?new Set(parsed.map((r)=>r[pageKey]).filter(Boolean)).size:null};
  for(const days of [7,30,90]){
    const beforeStart=new Date(change.getTime()-days*86400000);
    const afterEnd=new Date(change.getTime()+days*86400000);
    const before=parsed.filter((r)=>r.__date>=beforeStart&&r.__date<change);
    const after=parsed.filter((r)=>r.__date>=change&&r.__date<afterEnd);
    const clicksBefore=sum(before,clicksKey), clicksAfter=sum(after,clicksKey);
    const impBefore=sum(before,impressionsKey), impAfter=sum(after,impressionsKey);
    const sessionsBefore=sum(before,sessionsKey), sessionsAfter=sum(after,sessionsKey);
    result.windows.push({
      days,
      rowsBefore:before.length,rowsAfter:after.length,
      clicksBefore,clicksAfter,impressionsBefore:impBefore,impressionsAfter:impAfter,
      ctrBefore:impBefore?clicksBefore/impBefore*100:null,ctrAfter:impAfter?clicksAfter/impAfter*100:null,
      positionBefore:avg(before,positionKey),positionAfter:avg(after,positionKey),
      sessionsBefore,sessionsAfter
    });
  }
  return result;
}
function analyticsV2(){
  setTitle('Analytics & AI Visibility','Compare exported evidence before and after a change without pretending Google accounts are connected.');
  view.innerHTML=
    '<div class="callout section"><b>Data boundary:</b> CSV files are read locally in your browser. This demo does not authenticate to Search Console or Google Analytics.</div>'+
    '<div class="grid two section"><div class="card"><h2>1 · Choose change date</h2><input id="changeDate" type="date" value="2026-09-01"><p class="muted mini">The app compares 7-, 30-, and 90-day windows before/after this date when the CSV contains those dates.</p></div>'+
      '<div class="card"><h2>2 · Import export</h2><input id="metricCsv" type="file" accept=".csv,text/csv"><p class="muted mini">Recognizes common columns such as Date, Clicks, Impressions, Position, Sessions, Page/Landing Page.</p><button id="loadMetricDemo" class="secondary">Use synthetic demo CSV</button></div></div>'+
    '<div id="analyticsOut"><div class="card"><h2>Comparison report</h2><p class="muted">Import a CSV or load the synthetic demo.</p></div></div>';
  const run=async(text,label)=>{
    try{
      const rows=parseCsv(text);
      const summary=summarizeCsvRows(rows,document.getElementById('changeDate').value);
      renderAnalyticsSummary(summary,label);
    }catch(error){document.getElementById('analyticsOut').innerHTML='<div class="card"><h2>CSV review</h2><p class="bad">'+esc(error.message)+'</p></div>';}
  };
  document.getElementById('metricCsv').onchange=async(e)=>{const file=e.target.files?.[0];if(file) run(await file.text(),file.name);};
  document.getElementById('loadMetricDemo').onclick=()=>{
    const rows=['Date,Clicks,Impressions,Position,Sessions,Page'];
    const start=new Date('2026-06-01T00:00:00Z');
    for(let i=0;i<190;i++){
      const d=new Date(start.getTime()+i*86400000);
      const after=d>=new Date('2026-09-01T00:00:00Z');
      rows.push([d.toISOString().slice(0,10),Math.round(110+(after?24:0)+(i%11)),Math.round(2700+(after?320:0)+(i%17)*8),(after?18.3:21.2)-(i%5)*0.08,Math.round(160+(after?27:0)+(i%9)),'/programs/health-sciences'].join(','));
    }
    run(rows.join('\n'),'Synthetic demo data');
  };
}
function fmtMetric(v,digits=1){return v===null||v===undefined?'—':Number(v).toFixed(digits);}
function renderAnalyticsSummary(s,label){
  const rows=s.windows.map((w)=>'<tr><td><b>'+w.days+' days</b></td><td>'+fmtMetric(w.clicksBefore,0)+' → '+fmtMetric(w.clicksAfter,0)+'</td><td>'+fmtMetric(w.impressionsBefore,0)+' → '+fmtMetric(w.impressionsAfter,0)+'</td><td>'+fmtMetric(w.ctrBefore,2)+'% → '+fmtMetric(w.ctrAfter,2)+'%</td><td>'+fmtMetric(w.positionBefore,1)+' → '+fmtMetric(w.positionAfter,1)+'</td><td>'+fmtMetric(w.sessionsBefore,0)+' → '+fmtMetric(w.sessionsAfter,0)+'</td></tr>').join('');
  const w30=s.windows.find((w)=>w.days===30);
  const clicksDelta=w30&&w30.clicksBefore?((w30.clicksAfter-w30.clicksBefore)/w30.clicksBefore*100):null;
  const narrative='For the 30-day comparison around '+s.changeDate+', '+(clicksDelta===null?'click data were unavailable.':('clicks changed '+(clicksDelta>=0?'+':'')+clicksDelta.toFixed(1)+'%.'))+' Treat this as descriptive evidence, not proof that one change caused the movement.';
  document.getElementById('analyticsOut').innerHTML=
    '<div class="card section"><div class="eyebrow">'+esc(label.toUpperCase())+'</div><h2>Baseline → post-change comparison</h2><p class="muted">Change date: '+esc(s.changeDate)+(s.affectedPages!==null?' · '+s.affectedPages+' affected page(s) represented':'')+'</p><div class="table-wrap"><table><tr><th>Window</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Avg. position</th><th>Sessions/users</th></tr>'+rows+'</table></div><div class="callout" style="margin-top:14px">'+esc(narrative)+'</div><div class="header-actions" style="margin-top:12px"><button id="copyAnalyticsNarrative" class="secondary">Copy plain-English report</button><button id="printAnalytics" class="secondary">Print / Save as PDF</button></div></div>';
  document.getElementById('copyAnalyticsNarrative').onclick=()=>navigator.clipboard.writeText(narrative);
  document.getElementById('printAnalytics').onclick=()=>window.print();
}

function progressReporting(){
  setTitle('Progress & Reporting','Track ownership, evidence, status, expected impact, actual result, and next review.');
  const items=[
    ['Admissions','Program-page metadata cleanup','Web','Completed','High','Meta/title changes verified','2026-10-09'],
    ['Research','Faculty schema pilot','Comms','Active','High','Pilot validation pending','2026-10-06'],
    ['Education','Heading hierarchy cleanup','Dept. editor','Active','Medium','3 pages reviewed','2026-10-07'],
    ['Legacy PDFs','Document inventory review','Web + owners','Queued','High','— pending','2026-10-15'],
    ['News','Article author/date consistency','Editors','Completed','Medium','Template guidance published','2026-10-12'],
    ['Admissions','Redirect chain cleanup','Web Architect','Active','High','Chain checks underway','2026-10-05'],
    ['Student Affairs','Internal-link improvements','Dept. editor','Queued','Medium','— pending','2026-10-14'],
    ['Cross-site','Editor mini-course','Web','Completed','Medium','Training draft ready','2026-10-11']
  ];
  view.innerHTML=
    '<div class="grid three section">'+kpi('Roadmap','24 items','illustrative portfolio workload')+kpi('Completed','7','documented change evidence')+kpi('Active / queued','5 / 12','owner-aware backlog')+'</div>'+
    '<div class="card section"><h2>Roadmap register</h2><div class="table-wrap"><table><tr><th>Area</th><th>Work</th><th>Owner</th><th>Status</th><th>Expected impact</th><th>Actual result / evidence</th><th>Next review</th></tr>'+
      items.map((r)=>'<tr>'+r.map((x,i)=>'<td>'+(i===0?'<b>'+esc(x)+'</b>':esc(x))+'</td>').join('')+'</tr>').join('')+
    '</table></div></div>'+
    '<div class="grid two section"><div class="card"><h2>Weekly Web Architect update</h2><textarea id="weeklyUpdate" aria-label="Generated weekly update"></textarea><div class="header-actions" style="margin-top:10px"><button id="generateWeekly" class="primary">Generate weekly update</button><button id="copyWeekly" class="secondary">Copy</button></div></div>'+
      '<div class="card"><h2>Export</h2><p class="muted">JSON and CSV keep the register machine-readable. Print uses the browser’s Save as PDF workflow.</p><div class="header-actions"><button id="reportJson" class="secondary">Export JSON</button><button id="reportCsv" class="secondary">Export CSV</button><button id="reportPdf" class="secondary">Print / Save as PDF</button></div></div></div>';
  const generate=()=>{
    const completed=items.filter((r)=>r[3]==='Completed');
    const active=items.filter((r)=>r[3]==='Active');
    const queued=items.filter((r)=>r[3]==='Queued');
    document.getElementById('weeklyUpdate').value=
      'SearchSignal weekly web-operations update\\n\\nCompleted: '+completed.map((r)=>r[0]+' — '+r[1]).join('; ')+
      '\\n\\nActive: '+active.map((r)=>r[0]+' — '+r[1]+' (next review '+r[6]+')').join('; ')+
      '\\n\\nQueued: '+queued.map((r)=>r[0]+' — '+r[1]).join('; ')+
      '\\n\\nEvidence boundary: this portfolio register is illustrative. Production results would be populated from approved change logs and measurement sources.';
  };
  generate();
  document.getElementById('generateWeekly').onclick=generate;
  document.getElementById('copyWeekly').onclick=()=>navigator.clipboard.writeText(document.getElementById('weeklyUpdate').value);
  document.getElementById('reportJson').onclick=()=>downloadFile('searchsignal-roadmap.json',JSON.stringify(items,null,2),'application/json');
  document.getElementById('reportCsv').onclick=()=>downloadFile('searchsignal-roadmap.csv',[['area','work','owner','status','expected impact','result evidence','next review']].concat(items).map((r)=>r.map(csvCell).join(',')).join('\\n'),'text/csv');
  document.getElementById('reportPdf').onclick=()=>window.print();
}

function scaleSimulator(){
  setTitle('20K Scale Simulator','Model batching, rate limits, caching, checkpoints, and prioritization without crawling Geisel.');
  view.innerHTML=
    '<div class="callout section"><b>Synthetic workload only:</b> this simulator does not crawl Geisel or any external site. It models the mechanics of handling a 20,000-page / 15,000-document inventory.</div>'+
    '<div class="grid two section"><div class="card"><h2>Inventory model</h2><label>Pages<input id="scalePages" type="number" min="100" max="100000" value="20000"></label><br><label>Documents<input id="scaleDocs" type="number" min="0" max="100000" value="15000"></label><br><label>Batch size<input id="scaleBatch" type="number" min="10" max="1000" value="250"></label><br><label>Rate / sec<input id="scaleRate" type="number" min="0.5" max="20" step="0.5" value="4"></label><div class="header-actions" style="margin-top:12px"><button id="scaleRunBtn" class="primary">Run simulation</button><button id="scalePause" class="secondary" disabled>Pause</button><button id="scaleResume" class="secondary" disabled>Resume</button></div></div>'+
      '<div class="card"><h2>Execution progress</h2><div class="progress-track"><div id="scaleBar" class="progress-bar" style="width:0%"></div></div><div id="scaleProgress" class="metric">0%</div><p id="scaleProgressNote" class="muted">Ready.</p></div></div>'+
    '<div id="scaleOut"></div>';
  let timer=null;let progress=0;let current=null;
  const tick=()=>{
    progress=Math.min(100,progress+4);
    document.getElementById('scaleBar').style.width=progress+'%';
    document.getElementById('scaleProgress').textContent=progress+'%';
    document.getElementById('scaleProgressNote').textContent=progress<100?'Processing synthetic batches with checkpoints and cache lookups…':'Simulation complete. No external crawl was performed.';
    if(progress>=100){clearInterval(timer);timer=null;document.getElementById('scalePause').disabled=true;document.getElementById('scaleResume').disabled=true;}
  };
  document.getElementById('scaleRunBtn').onclick=async()=>{
    try{
      const r=await fetch('/api/scale-sim',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({pages:Number(document.getElementById('scalePages').value),documents:Number(document.getElementById('scaleDocs').value),batchSize:Number(document.getElementById('scaleBatch').value),ratePerSecond:Number(document.getElementById('scaleRate').value)})});
      current=await r.json();if(!r.ok) throw new Error(current.error||'Simulation failed');state.scaleRun=current;
      renderScaleResult(current);progress=0;tick();if(timer)clearInterval(timer);timer=setInterval(tick,120);
      document.getElementById('scalePause').disabled=false;document.getElementById('scaleResume').disabled=true;
    }catch(error){document.getElementById('scaleOut').innerHTML='<div class="card"><p class="bad">'+esc(error.message)+'</p></div>';}
  };
  document.getElementById('scalePause').onclick=()=>{if(timer){clearInterval(timer);timer=null;}document.getElementById('scalePause').disabled=true;document.getElementById('scaleResume').disabled=false;document.getElementById('scaleProgressNote').textContent='Paused at checkpoint-safe simulated state.';};
  document.getElementById('scaleResume').onclick=()=>{if(!timer&&progress<100)timer=setInterval(tick,120);document.getElementById('scalePause').disabled=false;document.getElementById('scaleResume').disabled=true;};
}
function renderScaleResult(d){
  const i=d.issueCounts;
  document.getElementById('scaleOut').innerHTML=
    '<div class="grid three section">'+kpi('Total inventory',d.inventory.totalItems.toLocaleString(),d.inventory.pages.toLocaleString()+' pages + '+d.inventory.documents.toLocaleString()+' docs')+kpi('Batches',d.execution.batches,d.execution.batchSize+' items / batch')+kpi('Rate limit',d.execution.ratePerSecond+'/s',Math.ceil(d.execution.estimatedSeconds/60)+' min modeled runtime')+'</div>'+
    '<div class="grid two section"><div class="card"><h2>Synthetic pattern output</h2><table><tr><th>Pattern</th><th>Modeled count</th></tr>'+
      [['Duplicate titles',i.duplicateTitles],['Broken links',i.brokenLinks],['Redirect chains',i.redirectChains],['Missing canonicals',i.missingCanonicals],['Orphaned documents',i.orphanedDocuments],['Oversized documents',i.oversizedDocuments]].map((x)=>'<tr><td>'+x[0]+'</td><td><b>'+x[1].toLocaleString()+'</b></td></tr>').join('')+'</table></div>'+
      '<div class="card"><h2>Execution controls</h2><p><b>Cache:</b> '+esc(d.execution.cacheStrategy)+'</p><p><b>Checkpoint:</b> every '+d.execution.checkpointEveryBatches+' batches</p><p><b>Resume cursor:</b> '+d.execution.resumeFrom.toLocaleString()+'</p><h3>Priority preview</h3>'+d.queuePreview.map((x)=>'<div class="check"><span class="status work">'+x.priority+'</span><span>'+esc(x.work)+'</span><span></span></div>').join('')+'</div></div>'+
    '<div class="callout section">'+esc(d.boundary)+'</div>';
}

function coverageV2(){
  setTitle('Requirements Coverage','Open each requirement to see implementation, automated-test, and live-verification evidence separately.');
  const rows=[
    {name:'Technical/content SEO audits',evidence:'Live URL Auditor inspects metadata, indexability, canonical, headings, links, schema, image-alt coverage, generic-link text and form-label signals.',implemented:true,tested:true,live:true,date:'2026-09-30',notes:'Public audit endpoint live-verified. Accessibility items are heuristic signals, not conformance claims.'},
    {name:'Find → fix → verify implementation',evidence:'Change Lab demonstrates a synthetic page moving from detected issue to exact safe change, validation, and re-audit.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Sandbox-only by design; no production site is modified.'},
    {name:'Site pattern detection',evidence:'Site Patterns converts bounded crawl results into duplicate-title, canonical, H1, and document-link clusters.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Counts stay scoped to the bounded sample.'},
    {name:'Document operations',evidence:'Document Intelligence tracks HTTP status, file size, Last-Modified, duplicate filenames, weak link text, and referencing pages.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Accessibility and true orphan status require separate review/broader inventory.'},
    {name:'Redirect validation',evidence:'Redirect validator shows each hop and now detects loops before the eight-hop safety cap.',implemented:true,tested:true,live:true,date:'2026-09-30',notes:'Public chain behavior verified on hosted build; loop detection added in this upgrade.'},
    {name:'WordPress end-user support',evidence:'Interactive support scenarios produce diagnosis, editor-safe steps, escalation, plain-language response, and KB draft.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Support simulation; no live admin connection claimed.'},
    {name:'Search/analytics measurement',evidence:'Browser-local CSV workflow compares 7/30/90-day windows around a change date and generates a plain-English report.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'No authenticated Google access is represented.'},
    {name:'Progress reporting',evidence:'Roadmap register tracks owner, status, expected impact, evidence/result, and next review; weekly update generator included.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Illustrative register until connected to an approved production change log.'},
    {name:'Large decentralized environment',evidence:'20K/15K synthetic scale simulator models batching, rate limits, caching, checkpoints, pause/resume, and prioritization.',implemented:true,tested:true,live:false,date:'2026-10-02',notes:'Synthetic workload only; intentionally does not crawl Geisel at scale.'},
    {name:'Training & documentation',evidence:'Training Center provides editor-focused mini-modules with plain-language guidance and escalation rules.',implemented:true,tested:true,live:true,date:'2026-09-30',notes:'Portfolio training content is visible in the hosted build.'}
  ];
  const badge=(label,on)=>'<span class="evidence-pill '+(on?'yes':'pending')+'">'+label+': '+(on?'Yes':'Pending')+'</span>';
  view.innerHTML=
    '<div class="card section"><h2>Evidence states</h2><p class="muted"><b>Implemented</b> means code exists. <b>Automated test</b> means the QA suite contains a check for the capability. <b>Live verified</b> is kept separate and is not marked until the deployed surface has been exercised.</p></div>'+
    '<div class="coverage-list">'+rows.map((r)=>'<details class="card coverage-item"><summary><span><b>'+esc(r.name)+'</b><span class="muted mini">'+esc(r.evidence)+'</span></span><span class="coverage-badges">'+badge('Implemented',r.implemented)+badge('Automated test',r.tested)+badge('Live verified',r.live)+'</span></summary><div class="coverage-detail"><p>'+esc(r.notes)+'</p><p class="muted mini">Verification / implementation date: '+esc(r.date)+'</p></div></details>').join('')+'</div>'+
    '<div class="callout section"><b>Accuracy boundary:</b> implementation, automated verification, hosted/live verification, and production experience are deliberately separate claims.</div>';
}

window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(pages.some((p)=>p[0]===id))show(id);});
const initialPage=location.hash.slice(1);
show(pages.some((p)=>p[0]===initialPage)?initialPage:'interview');