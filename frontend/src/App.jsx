import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, Bot, BrainCircuit, Calculator, CheckCircle2, ChevronRight, Clock3,
  Database, FileSearch, FileText, Gauge, GitBranch, Headphones, Image, LayoutDashboard,
  LoaderCircle, Mail, Phone, Plus, RefreshCw, ShieldCheck, Trash2, Upload, Users, XCircle,
} from "lucide-react";
import { assignClaim, createClaim, createContact, deleteContact, getClaim, getSystemInfo, listClaims, listContacts, notifyResponsible, retryClaim, updateClaimFiles } from "./api";

const EMPTY_FORM = {
  customer_name: "",
  policy_number: "",
  incident_date: "",
  location: "",
  description: "",
};

const statusLabels = {
  SUBMITTED: "Soumis",
  PROCESSING: "Analyse en cours",
  COMPLETED: "Terminé",
  FAILED: "Échec",
};

const decisionInfo = {
  ACCEPT: { label: "Accepté", icon: CheckCircle2, className: "accept" },
  INVESTIGATE: { label: "À examiner", icon: AlertTriangle, className: "investigate" },
  REJECT: { label: "Refusé", icon: XCircle, className: "reject" },
};

function App() {
  const [claims, setClaims] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [view, setView] = useState("dashboard");
  const [systemInfo, setSystemInfo] = useState(null);
  const [supplementClaim, setSupplementClaim] = useState(null);
  const [supplementFiles, setSupplementFiles] = useState([]);
  const [contacts, setContacts] = useState([]);

  async function refreshClaims() {
    try {
      const data = await listClaims();
      setClaims(data.results || data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refreshClaims();
    listContacts().then(setContacts).catch((err) => setError(err.message));
    getSystemInfo().then(setSystemInfo).catch((err) => setError(err.message));
  }, []);

  const pollTargetId = selected && ["SUBMITTED", "PROCESSING"].includes(selected.status)
    ? selected.id
    : view === "trace" ? claims.find((item) => ["SUBMITTED", "PROCESSING"].includes(item.status))?.id : null;

  useEffect(() => {
    if (!pollTargetId) return;
    const timer = setInterval(async () => {
      try {
        const updated = await getClaim(pollTargetId);
        setSelected((current) => current?.id === updated.id || (view === "trace" && !current) ? updated : current);
        setClaims((current) => current.map((item) => item.id === updated.id ? updated : item));
      } catch (err) {
        setError(err.message);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [pollTargetId, view]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const created = await createClaim(form, files);
      setClaims((current) => [created, ...current]);
      setSelected(created);
      setForm(EMPTY_FORM);
      setFiles([]);
      setShowForm(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitSupplement(event, keepDocumentIds) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const updated = await updateClaimFiles(supplementClaim.id, supplementFiles, keepDocumentIds);
      setSelected(updated);
      setClaims((current) => current.map((item) => item.id === updated.id ? updated : item));
      setSupplementClaim(null);
      setSupplementFiles([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitContact(values) {
    try {
      const created = await createContact(values);
      setContacts((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }

  async function removeContact(contact) {
    const hasAssignedClaims = claims.some((claim) => String(claim.assigned_contact?.id) === String(contact.id));
    const impact = hasAssignedClaims
      ? " Les dossiers déjà attribués resteront, mais leur attribution à ce contact sera retirée."
      : "";
    if (!window.confirm(`Supprimer ${contact.name} du répertoire ?${impact}`)) return;
    try {
      await deleteContact(contact.id);
      setContacts((current) => current.filter((item) => String(item.id) !== String(contact.id)));
      const unassign = (claim) => String(claim.assigned_contact?.id) === String(contact.id)
        ? { ...claim, assigned_contact: null }
        : claim;
      setClaims((current) => current.map(unassign));
      setSelected((current) => current ? unassign(current) : current);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handoffClaim(claimId, contactId, note) {
    try {
      const updated = await assignClaim(claimId, contactId, note);
      setSelected(updated);
      setClaims((current) => current.map((item) => item.id === updated.id ? updated : item));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }

  async function resendHandoffEmail(claimId) {
    try {
      const updated = await notifyResponsible(claimId);
      setSelected(updated);
      setClaims((current) => current.map((item) => item.id === updated.id ? updated : item));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }

  const metrics = useMemo(() => ({
    total: claims.length,
    processing: claims.filter((x) => ["SUBMITTED", "PROCESSING"].includes(x.status)).length,
    accepted: claims.filter((x) => x.decision === "ACCEPT").length,
    flagged: claims.filter((x) => x.decision === "INVESTIGATE").length,
  }), [claims]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><ShieldCheck size={25} /></span>
          <div><strong>AI Claims</strong><small>Automatisation des sinistres</small></div>
        </div>
        <div className="top-actions">
          <nav className="view-switcher">
            <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}><LayoutDashboard size={17} /> Dossiers</button>
            <button className={view === "trace" ? "active" : ""} onClick={() => setView("trace")}><GitBranch size={17} /> Traçabilité</button>
            <button className={view === "contacts" ? "active" : ""} onClick={() => setView("contacts")}><Users size={17} /> Contacts</button>
          </nav>
          <button className="primary" onClick={() => setShowForm(true)}><Plus size={18} /> Nouveau sinistre</button>
        </div>
      </header>

      <main>
        {view === "dashboard" ? <>
        <section className="hero">
          <div>
            <span className="eyebrow">WORKFLOW AUTONOME</span>
            <h1>Chaque dossier analysé,<br />de la déclaration à la décision.</h1>
            <p>Documents, photos et garanties sont contrôlés automatiquement par des agents spécialisés orchestrés avec n8n.</p>
          </div>
          <div className="agent-flow" aria-label="Étapes du workflow">
            <span><FileSearch />Document</span><ChevronRight />
            <span><Image />Vision</span><ChevronRight />
            <span><ShieldCheck />Policy RAG</span><ChevronRight />
            <span><Bot />Décision</span>
          </div>
        </section>

        {error && <div className="error-banner">{error}<button onClick={() => setError("")}>×</button></div>}

        <section className="metrics">
          <Metric label="Dossiers" value={metrics.total} />
          <Metric label="En traitement" value={metrics.processing} tone="blue" />
          <Metric label="Acceptés" value={metrics.accepted} tone="green" />
          <Metric label="À examiner" value={metrics.flagged} tone="orange" />
        </section>

        <section className="workspace">
          <div className="claims-panel">
            <div className="section-title"><div><h2>Dossiers récents</h2><p>Suivi en temps réel du workflow</p></div><button className="icon-button" onClick={refreshClaims}><RefreshCw size={17} /></button></div>
            <div className="claim-list">
              {claims.length === 0 && <div className="empty">Aucun dossier. Créez le premier sinistre.</div>}
              {claims.map((claim) => <ClaimRow key={claim.id} claim={claim} active={selected?.id === claim.id} onClick={() => setSelected(claim)} />)}
            </div>
          </div>
          <div className="detail-panel">
            {selected ? <ClaimDetail claim={selected} contacts={contacts} onHandoff={handoffClaim} onNotify={resendHandoffEmail} onRetry={async () => setSelected(await retryClaim(selected.id))} onAddFiles={() => setSupplementClaim(selected)} /> : <div className="empty detail-empty"><Bot size={38} /><h3>Sélectionnez un dossier</h3><p>La décision et les preuves apparaîtront ici.</p></div>}
          </div>
        </section>
        </> : view === "trace" ? <TracePage systemInfo={systemInfo} claims={claims} selected={selected} setSelected={setSelected} /> : <ContactsPage contacts={contacts} claims={claims} onCreateContact={submitContact} onDeleteContact={removeContact} onSelectClaim={(claim) => { setSelected(claim); setView("dashboard"); }} />}
      </main>

      {showForm && <ClaimModal form={form} setForm={setForm} files={files} setFiles={setFiles} busy={busy} onSubmit={submit} onClose={() => setShowForm(false)} />}
      {supplementClaim && <SupplementModal claim={supplementClaim} files={supplementFiles} setFiles={setSupplementFiles} busy={busy} onSubmit={submitSupplement} onClose={() => { setSupplementClaim(null); setSupplementFiles([]); }} />}
    </div>
  );
}

function TracePage({ systemInfo, claims, selected, setSelected }) {
  const observed = selected || claims.find((item) => item.status === "PROCESSING" || item.status === "SUBMITTED") || claims.find((item) => item.status === "COMPLETED");
  const timeline = observed?.agent_results?.timeline;
  const results = observed?.agent_results || {};
  const decisionResult = results.decision || {};
  const fraud = results.fraud || {};

  if (!systemInfo) return <div className="trace-loading"><LoaderCircle className="spin" /> Chargement de l'architecture...</div>;

  return <div className="trace-page">
    <section className="trace-hero">
      <div><span className="eyebrow">OBSERVABILITÉ DU WORKFLOW</span><h1>Comment les agents prennent leur décision</h1><p>Cette page montre le moteur utilisé, les entrées, les sorties et les calculs. Aucun LLM externe n'est encore branché dans le MVP.</p></div>
      <div className="automation-card"><GitBranch /><div><span>Orchestrateur</span><strong>{systemInfo.automation.engine}</strong><small>{systemInfo.automation.mode}</small></div></div>
    </section>

    <section className="trace-selector">
      <label>Dossier observé
        <select value={observed?.id || ""} onChange={(e) => setSelected(claims.find((item) => item.id === e.target.value) || null)}>
          <option value="">Architecture générale</option>
          {claims.map((claim) => <option key={claim.id} value={claim.id}>{claim.customer_name} · {claim.status}</option>)}
        </select>
      </label>
      {observed && (observed.status === "COMPLETED" ? <div className="trace-summary"><span>Décision</span><strong>{observed.decision}</strong><span>Risque</span><strong>{observed.risk_score == null ? "Non évalué" : `${observed.risk_score}/100`}</strong><span>Confiance</span><strong>{Math.round((observed.confidence || 0) * 100)}%</strong></div> : <div className="trace-summary"><span>État</span><strong>{statusLabels[observed.status]}</strong></div>)}
    </section>

    <section className="timeline-section">
      <div className="trace-title"><GitBranch /><div><h2>Timeline des agents</h2><p>Les trois premiers agents s'exécutent en parallèle, puis leurs résultats sont fusionnés. Les durées restantes sont estimatives.</p></div></div>
      {timeline && <WorkflowProgress timeline={timeline} />}
      <div className="timeline">
        <div className="parallel-group">
          <span className="phase-label">Phase 1 · Parallèle</span>
          <div className="parallel-agents">{systemInfo.agents.filter((a) => a.order === 1).map((agent) => <AgentCard key={agent.key} agent={agent} result={results[agent.key]} progress={timeline?.agents?.[agent.key]} />)}</div>
        </div>
        <div className="timeline-arrow">↓ Fusion des résultats</div>
        {systemInfo.agents.filter((a) => a.order > 1).map((agent) => <div key={agent.key} className="sequential-step"><span className="phase-label">Phase {agent.order} · Séquentielle</span><AgentCard agent={agent} result={agent.key === "decision" ? decisionResult : results[agent.key]} progress={timeline?.agents?.[agent.key]} /></div>)}
      </div>
    </section>

    {observed && <section className="attachments-section"><div className="trace-title"><FileText /><div><h2>Pièces de ce dossier</h2><p>Fichiers transmis avec la déclaration de {observed.customer_name}.</p></div></div><ClaimAttachments documents={observed.documents || []} /></section>}

    <section className="trace-grid">
      <article className="explain-card rag-card">
        <div className="trace-title"><Database /><div><h2>Corpus du Policy RAG</h2><p>{systemInfo.rag.mode}</p></div></div>
        <div className="truth-banner"><ShieldCheck />Le RAG interroge le contrat automobile officiel AXA indexé localement.</div>
        <dl className="tech-list"><div><dt>Modèle d'embeddings</dt><dd>{systemInfo.rag.embedding_model || "Aucun"}</dd></div><div><dt>Vector store</dt><dd>{systemInfo.rag.vector_store || "Aucun"}</dd></div><div><dt>Recherche</dt><dd>{systemInfo.rag.retrieval}</dd></div></dl>
        <div className="corpus-list">{systemInfo.rag.documents.map((doc) => <div key={doc.url || doc.title}><strong>{doc.title}</strong><span>{doc.insurer} · {doc.version}</span><p>{doc.pages} pages · <a href={doc.url} target="_blank" rel="noreferrer">source officielle</a></p></div>)}</div>
        {results.policy?.references?.length > 0 && <div className="used-evidence"><strong>Passages utilisés pour ce dossier</strong>{results.policy.references.map((ref, index) => <p key={`${ref.page}-${index}`}>Page {ref.page || "?"} · {ref.section || ref.source} · {ref.text}</p>)}</div>}
      </article>

      <article className="explain-card">
        <div className="trace-title"><Calculator /><div><h2>Calcul du score de risque</h2><p>{systemInfo.risk.formula}</p></div></div>
        <div className="formula">Risque = min(100, Σ points)</div>
        <div className="rule-list">{systemInfo.risk.rules.map((rule) => <div key={rule.key}><span>{rule.label}</span><strong>+{rule.points}</strong></div>)}</div>
        <div className="calculation-result"><Gauge /><div><span>Calcul de ce dossier</span>{fraud.score_breakdown?.length ? fraud.score_breakdown.map((item) => <p key={item.rule}>+{item.points} · {item.evidence}</p>) : fraud.assessment_status === "incomplete" ? <p>Analyse incomplète : le score n'est pas évalué.</p> : <p>Aucune incohérence détectée : +0</p>}<strong>Total : {observed?.risk_score == null ? "Non évalué" : `${observed.risk_score}/100`}</strong></div></div>
      </article>

      <article className="explain-card">
        <div className="trace-title"><BrainCircuit /><div><h2>Calcul de la confiance</h2><p>La confiance mesure la qualité des preuves disponibles.</p></div></div>
        <div className="formula">Confiance = base 95% - pénalités</div>
        <div className="rule-list">{systemInfo.confidence.penalties.map((penalty) => <div key={penalty.label}><span>{penalty.label}</span><strong>-{typeof penalty.value === "number" ? `${Math.round(penalty.value * 100)}%` : penalty.value}</strong></div>)}</div>
        {decisionResult.confidence_breakdown && <div className="calculation-result"><CheckCircle2 /><div><span>Calcul de ce dossier</span>{decisionResult.confidence_breakdown.penalties.map((item) => <p key={item.reason}>-{Math.round(item.value * 100)}% · {item.reason}</p>)}<strong>Résultat : {Math.round(decisionResult.confidence_breakdown.result * 100)}%</strong></div></div>}
      </article>
    </section>
  </div>;
}

function AgentCard({ agent, result, progress }) {
  const running = progress?.status === "RUNNING";
  const completed = progress?.status === "COMPLETED" || Boolean(result);
  const failed = progress?.status === "FAILED";
  const label = running ? "En cours" : completed ? "Terminé" : failed ? "Échec" : "En attente";
  const actualEngine = result?.engine === "local-fallback" ? "Fallback local" : result?.engine || agent.engine;
  const actualModel = result?.engine === "local-fallback" ? "Non utilisé (fallback)" : result?.model || agent.llm || "Aucun LLM dans le MVP";
  return <article className={`agent-card ${result ? "has-result" : ""}`}>
    <div className="agent-card-head"><span className="agent-icon">{running ? <LoaderCircle className="spin" /> : <Bot />}</span><div><h3>{agent.name}</h3><span className={running ? "agent-running" : failed ? "agent-failed" : ""}>{progress ? label : agent.status}</span></div></div>
    {progress && <AgentProgress progress={progress} />}
    <dl><div><dt>Moteur utilisé</dt><dd>{actualEngine}</dd></div><div><dt>LLM utilisé</dt><dd>{actualModel}</dd></div><div><dt>Entrée</dt><dd>{agent.input}</dd></div><div><dt>Sortie</dt><dd>{agent.output}</dd></div></dl>
    {result?.pdf_extraction_comparison?.length > 0 && <section className="pdf-comparison"><h4>Comparaison PDF : pypdf et OCR</h4>{result.pdf_extraction_comparison.map((pdf) => <details key={pdf.file}><summary>{pdf.file} · {pdf.status === "compared" ? `similarité ${pdf.similarity == null ? "—" : `${Math.round(pdf.similarity * 100)}%`}` : pdf.error ? "OCR indisponible" : "pypdf indisponible"} · texte retenu : {pdf.selected_method}</summary>{pdf.pypdf_error && <p>{pdf.pypdf_error}</p>}{pdf.error && <p>{pdf.error}</p>}<p><strong>pypdf ({pdf.pypdf_characters} caractères)</strong></p><pre>{pdf.pypdf_excerpt || "Aucun texte extrait par pypdf."}</pre><p><strong>OCR Tesseract ({pdf.ocr_characters} caractères)</strong></p><pre>{pdf.ocr_excerpt || "Aucun texte extrait par OCR."}</pre><p><strong>Texte identique retrouvé dans les deux</strong></p><pre>{pdf.shared_text || "Aucun segment identique suffisamment long ; vérifier les deux extractions ci-dessus."}</pre></details>)}</section>}
    {result && <details><summary>Voir la sortie JSON</summary><pre>{JSON.stringify(result, null, 2)}</pre></details>}
  </article>;
}

function WorkflowProgress({ timeline }) {
  const agents = timeline.agents || {};
  const entries = Object.values(agents);
  const pending = entries.filter((item) => item.status === "PENDING").length;
  const running = entries.filter((item) => item.status === "RUNNING").length;
  const done = entries.filter((item) => item.status === "COMPLETED").length;
  const remaining = (item = {}) => {
    if (["COMPLETED", "FAILED"].includes(item.status)) return 0;
    if (item.status === "RUNNING" && item.started_at) return Math.max(0, (item.expected_seconds || 60) - Math.floor((Date.now() - new Date(item.started_at).getTime()) / 1000));
    return item.expected_seconds || 60;
  };
  const parallelEta = Math.max(remaining(agents.document), remaining(agents.vision), remaining(agents.policy));
  const sequentialEta = remaining(agents.fraud) + remaining(agents.decision);
  const parallelDone = ["document", "vision", "policy"].every((key) => ["COMPLETED", "FAILED"].includes(agents[key]?.status));
  const etaSeconds = (parallelDone ? 0 : parallelEta) + sequentialEta;
  return <div className="workflow-progress">
    <div><strong>{running ? `${running} agent(s) en cours` : done === entries.length && entries.length ? "Analyse terminée" : "Workflow en préparation"}</strong><span>{done}/{entries.length} terminés · {pending} en attente</span></div>
    <div className="workflow-eta"><Clock3 size={16} />Temps restant estimé : ~{formatDuration(etaSeconds)}</div>
    <small>Estimation indicative selon la durée prévue de chaque étape. Le temps réel dépend des fichiers et de la vitesse d’Ollama.</small>
  </div>;
}

function AgentProgress({ progress }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    if (progress.status !== "RUNNING") return undefined;
    const timer = setInterval(() => setTick((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [progress.status, progress.started_at]);
  const elapsed = progress.status === "COMPLETED" || progress.status === "FAILED"
    ? progress.elapsed_seconds || 0
    : progress.started_at ? Math.max(0, Math.floor((Date.now() - new Date(progress.started_at).getTime()) / 1000)) : 0;
  const remaining = Math.max(0, (progress.expected_seconds || 60) - elapsed);
  return <div className={`agent-progress ${progress.status?.toLowerCase() || "pending"}`}>
    <div className="agent-progress-meta"><span>{progress.status === "RUNNING" ? `En cours · ${formatDuration(elapsed)} écoulées` : progress.status === "COMPLETED" ? `Terminé en ${formatDuration(elapsed)}` : progress.status === "FAILED" ? `Échec après ${formatDuration(elapsed)}` : "En attente"}</span><span>{progress.status === "RUNNING" ? `reste ~${formatDuration(remaining)}` : `prévu ~${formatDuration(progress.expected_seconds || 60)}`}</span></div>
    <div className="agent-progress-track"><span style={{ width: progress.status === "COMPLETED" ? "100%" : progress.status === "RUNNING" ? `${Math.min(94, Math.max(8, elapsed / (progress.expected_seconds || 60) * 100))}%` : "0%" }} /></div>
  </div>;
}

function formatDuration(seconds) {
  const safe = Math.max(0, Math.floor(seconds || 0));
  if (safe < 60) return `${safe}s`;
  return `${Math.floor(safe / 60)} min ${String(safe % 60).padStart(2, "0")}s`;
}

function Metric({ label, value, tone = "neutral" }) {
  return <article className={`metric ${tone}`}><span>{label}</span><strong>{value}</strong></article>;
}

function ClaimRow({ claim, active, onClick }) {
  const decision = decisionInfo[claim.decision];
  return <button className={`claim-row ${active ? "active" : ""}`} onClick={onClick}>
    <span className="claim-id">#{claim.id.slice(0, 8).toUpperCase()}</span>
    <span className="claim-main"><strong>{claim.customer_name}</strong><small>{claim.location} · {claim.incident_date}</small></span>
    <span className={`status ${decision?.className || claim.status.toLowerCase()}`}>{decision?.label || statusLabels[claim.status]}</span>
    <ChevronRight size={17} />
  </button>;
}

function ClaimDetail({ claim, contacts, onRetry, onAddFiles, onHandoff, onNotify }) {
  const info = decisionInfo[claim.decision];
  const Icon = info?.icon || LoaderCircle;
  const [contactId, setContactId] = useState(claim.assigned_contact?.id || "");
  const [handoffNote, setHandoffNote] = useState(claim.handoff_note || "");
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [handoffMessage, setHandoffMessage] = useState("");
  useEffect(() => {
    setContactId(claim.assigned_contact?.id || "");
    setHandoffNote(claim.handoff_note || "");
  }, [claim.id, claim.assigned_contact?.id, claim.handoff_note]);
  async function submitHandoff(event) {
    event.preventDefault();
    if (!contactId) return;
    setHandoffBusy(true);
    setHandoffMessage("");
    try {
      const updated = await onHandoff(claim.id, contactId, handoffNote);
      setHandoffMessage(updated.handoff_email_status === "SENT" ? `Dossier transmis et email envoyé à ${updated.assigned_contact.email}.` : `Dossier attribué, mais email non envoyé : ${updated.handoff_email_error || "configuration email manquante."}`);
    } catch (err) {
      setHandoffMessage(err.message);
    } finally {
      setHandoffBusy(false);
    }
  }
  return <div className="detail-content">
    <div className="detail-heading">
      <div><span className="claim-id">DOSSIER #{claim.id.slice(0, 8).toUpperCase()}</span><h2>{claim.customer_name}</h2><p>{claim.policy_number} · {claim.location}</p></div>
      <span className={`decision-badge ${info?.className || "processing"}`}><Icon className={claim.status === "PROCESSING" ? "spin" : ""} />{info?.label || statusLabels[claim.status]}</span>
    </div>
    <div className="description"><span>Déclaration</span><p>{claim.description}</p></div>
    {claim.status === "FAILED" && <div className="failure"><p>{claim.error_message}</p><button className="secondary" onClick={onRetry}>Relancer n8n</button></div>}
    {["SUBMITTED", "PROCESSING"].includes(claim.status) && <div className="processing-card"><LoaderCircle className="spin" /><div className="processing-content"><strong>Analyse automatique en cours</strong><p>n8n coordonne les agents spécialisés.</p>{claim.agent_results?.timeline && <WorkflowProgress timeline={claim.agent_results.timeline} />}</div></div>}
    <ClaimAttachments documents={claim.documents || []} />
    {claim.status === "COMPLETED" && <>
      <div className="score-grid"><div><span>Confiance</span><strong>{Math.round((claim.confidence || 0) * 100)}%</strong></div><div><span>Risque</span><strong>{claim.risk_score == null ? "Non évalué" : `${claim.risk_score}/100`}</strong></div><div><span>Documents</span><strong>{claim.documents.length}</strong></div></div>
      <section className="evidence"><h3>Justification</h3>{claim.reasons.map((reason, index) => <p key={index}><CheckCircle2 size={17} />{reason}</p>)}</section>
      <section className="evidence contract-evidence"><h3>Références du contrat</h3>{claim.policy_references.length ? claim.policy_references.map((ref, index) => <details key={index}><summary><ShieldCheck size={17} />Page {ref.page || "?"} · {ref.section || ref.source}</summary><p>{ref.text}</p></details>) : <p>Aucune référence retournée.</p>}</section>
    </>}
    {claim.status === "COMPLETED" && claim.decision === "INVESTIGATE" && <section className="handoff-section">
      <div className="handoff-heading"><Users /><div><h3>Transmettre à un responsable</h3><p>Le responsable retrouvera ce dossier dans la page Contacts, avec ses pièces et l’analyse.</p></div></div>
      {claim.assigned_contact && <div className="assigned-contact"><CheckCircle2 size={17} /><span>Attribué à <strong>{claim.assigned_contact.name}</strong> · {claim.handoff_at ? new Date(claim.handoff_at).toLocaleString("fr-TN") : ""}<small className={`email-state ${claim.handoff_email_status?.toLowerCase() || ""}`}>{claim.handoff_email_status === "SENT" ? `Email envoyé${claim.handoff_email_sent_at ? ` le ${new Date(claim.handoff_email_sent_at).toLocaleString("fr-TN")}` : ""}` : claim.handoff_email_status === "FAILED" ? `Échec email : ${claim.handoff_email_error}` : claim.handoff_email_status === "NOT_CONFIGURED" ? claim.handoff_email_error : "Email pas encore envoyé"}</small></span></div>}
      {contacts.length ? <form onSubmit={submitHandoff} className="handoff-form">
        <label>Responsable<select value={contactId} onChange={(event) => setContactId(event.target.value)} required><option value="">Choisir un contact</option>{contacts.filter((contact) => contact.is_active).map((contact) => <option key={contact.id} value={contact.id}>{contact.name} · {contact.role}{contact.insurer ? ` — ${contact.insurer}` : ""}</option>)}</select></label>
        <label>Note de transmission<textarea rows="2" value={handoffNote} onChange={(event) => setHandoffNote(event.target.value)} placeholder="Pourquoi ce dossier nécessite une vérification…" /></label>
        <button className="primary" disabled={handoffBusy || !contactId}><Users size={16} />{handoffBusy ? "Transmission…" : claim.assigned_contact ? "Mettre à jour l’attribution" : "Transmettre le dossier"}</button>
        {claim.assigned_contact && <button type="button" className="secondary" disabled={handoffBusy} onClick={async () => { setHandoffBusy(true); try { const updated = await onNotify(claim.id); setHandoffMessage(updated.handoff_email_status === "SENT" ? `Email renvoyé à ${updated.assigned_contact.email}.` : updated.handoff_email_error || "Échec de l’envoi."); } catch (err) { setHandoffMessage(err.message); } finally { setHandoffBusy(false); } }}>Renvoyer l’email</button>}
        {handoffMessage && <p className="handoff-message">{handoffMessage}</p>}
      </form> : <p className="no-contacts">Ajoute d’abord les responsables dans la page Contacts.</p>}
    </section>}
    {["COMPLETED", "FAILED"].includes(claim.status) && <div className="detail-actions"><button className="primary" onClick={onAddFiles}><Upload size={17} />Gérer les pièces et relancer</button></div>}
  </div>;
}

function ClaimAttachments({ documents }) {
  if (!documents.length) return <section className="claim-attachments"><h3>Pièces du dossier</h3><p className="no-attachments">Aucun fichier joint à ce dossier.</p></section>;
  return <section className="claim-attachments"><h3>Pièces du dossier <span>{documents.length}</span></h3><div className="attachment-grid">{documents.map((document) => {
    const mime = document.mime_type || "";
    const url = document.file;
    const image = mime.startsWith("image/") || document.kind === "PHOTO";
    const audio = mime.startsWith("audio/") || document.kind === "AUDIO";
    const pdf = mime === "application/pdf" || document.original_name?.toLowerCase().endsWith(".pdf");
    return <article className="attachment-card" key={document.id}>
      {image && url ? <a href={url} target="_blank" rel="noreferrer" className="attachment-preview"><img src={url} alt={document.original_name} loading="lazy" /></a> : <div className="attachment-file-icon">{audio ? <Headphones /> : <FileText />}</div>}
      <div className="attachment-info"><strong title={document.original_name}>{document.original_name}</strong><span>{document.kind}{mime ? ` · ${mime}` : ""}</span>
        {audio && url && <audio controls preload="none" src={url}>Lecture audio non prise en charge.</audio>}
        {url && <div className="attachment-actions"><a href={url} target="_blank" rel="noreferrer">{pdf ? "Ouvrir le PDF" : image ? "Voir l’image" : "Ouvrir le fichier"}</a>{pdf && <details><summary>Aperçu</summary><iframe src={url} title={`Aperçu ${document.original_name}`} /> </details>}</div>}
      </div>
    </article>;
  })}</div></section>;
}

function ContactsPage({ contacts, claims, onCreateContact, onDeleteContact, onSelectClaim }) {
  const [form, setForm] = useState({ name: "", role: "Gestionnaire sinistres", insurer: "", email: "", phone: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const investigations = claims.filter((claim) => claim.decision === "INVESTIGATE");
  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await onCreateContact(form);
      setForm({ name: "", role: "Gestionnaire sinistres", insurer: "", email: "", phone: "" });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  }
  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }
  return <div className="contacts-page">
    <section className="trace-hero contacts-hero"><div><span className="eyebrow">ÉQUIPE DE GESTION</span><h1>Contacts assurance</h1><p>Ajoute les responsables réels de ton équipe, puis attribue-leur les dossiers qui nécessitent une vérification.</p></div><div className="automation-card"><Users /><div><span>Responsables</span><strong>{contacts.length}</strong><small>Dossiers à examiner : {investigations.length}</small></div></div></section>
    <div className="contacts-layout">
      <section className="contact-form-card"><div className="section-title"><div><h2>Ajouter un contact</h2><p>Renseigne les coordonnées de l’équipe assurance.</p></div></div>
        <form onSubmit={submit} className="contact-form">
          <label>Nom complet<input name="name" value={form.name} onChange={update} required /></label>
          <label>Fonction<input name="role" value={form.role} onChange={update} required /></label>
          <label>Compagnie d’assurance<input name="insurer" value={form.insurer} onChange={update} placeholder="Ex. assureur du contrat" /></label>
          <label>Email professionnel<input type="email" name="email" value={form.email} onChange={update} required /></label>
          <label>Téléphone<input type="tel" name="phone" value={form.phone} onChange={update} /></label>
          {formError && <p className="form-error">{formError}</p>}
          <button className="primary" disabled={saving}>{saving ? "Enregistrement…" : "Ajouter le contact"}</button>
        </form>
      </section>
      <section className="contact-directory"><div className="section-title"><div><h2>Répertoire</h2><p>Coordonnées enregistrées dans l’application.</p></div></div>
        {contacts.length ? <div className="contact-list">{contacts.map((contact) => <article className="contact-card" key={contact.id}><span className="contact-avatar"><Users /></span><div className="contact-main"><strong>{contact.name}</strong><span>{contact.role}{contact.insurer ? ` · ${contact.insurer}` : ""}</span><div className="contact-links">{contact.email && <a href={`mailto:${contact.email}`}><Mail size={14} />{contact.email}</a>}{contact.phone && <a href={`tel:${contact.phone}`}><Phone size={14} />{contact.phone}</a>}</div></div><div className="contact-card-actions"><span className={`contact-active ${contact.is_active ? "" : "inactive"}`}>{contact.is_active ? "Actif" : "Inactif"}</span><button type="button" className="delete-contact" aria-label={`Supprimer ${contact.name}`} title="Supprimer le contact" onClick={() => onDeleteContact(contact)}><Trash2 size={16} /></button></div></article>)}</div> : <div className="empty">Aucun contact enregistré. Ajoute les responsables de ton assurance.</div>}
      </section>
    </div>
    <section className="investigation-list"><div className="section-title"><div><h2>Dossiers à examiner</h2><p>Ouvre un dossier pour transmettre son analyse et ses pièces à un responsable.</p></div></div>
      {investigations.length ? <div className="handoff-claims">{investigations.map((claim) => <button key={claim.id} onClick={() => onSelectClaim(claim)}><span><strong>{claim.customer_name}</strong><small>#{claim.id.slice(0, 8).toUpperCase()} · {claim.policy_number} · Risque {claim.risk_score ?? "—"}/100</small></span><span className={claim.assigned_contact ? "assigned-label" : "unassigned-label"}>{claim.assigned_contact ? `Attribué à ${claim.assigned_contact.name}` : "À attribuer"}</span><ChevronRight size={17} /></button>)}</div> : <p className="empty">Aucun dossier ne nécessite une vérification pour le moment.</p>}
    </section>
  </div>;
}

function SupplementModal({ claim, files, setFiles, busy, onSubmit, onClose }) {
  const [keptIds, setKeptIds] = useState(() => claim.documents.map((document) => String(document.id)));
  const changed = files.length > 0 || keptIds.length !== claim.documents.length;
  const removeDocument = (documentId) => setKeptIds((current) => current.filter((id) => id !== String(documentId)));
  const replaceDocument = (documentId, replacement) => {
    if (!replacement) return;
    removeDocument(documentId);
    setFiles((current) => [...Array.from(current), replacement]);
  };
  const addFiles = (selectedFiles) => setFiles((current) => [...Array.from(current), ...Array.from(selectedFiles)]);
  return <div className="modal-backdrop">
    <form className="modal supplement-modal" onSubmit={(event) => onSubmit(event, keptIds)}>
      <div className="modal-header"><div><span className="eyebrow">DOSSIER #{claim.id.slice(0, 8).toUpperCase()}</span><h2>Gérer les pièces</h2></div><button type="button" className="close" onClick={onClose}>×</button></div>
      <p className="supplement-note">Conserve, remplace ou supprime les anciennes pièces, puis ajoute les nouvelles. La prochaine analyse utilisera uniquement la liste finale ci-dessous.</p>
      <div className="existing-files">
        <strong>Pièces actuelles</strong>
        {claim.documents.length === 0 && <p>Aucune pièce actuelle.</p>}
        {claim.documents.map((document) => keptIds.includes(String(document.id)) && <div className="file-editor-row" key={document.id}>
          <div><strong>{document.original_name}</strong><span>{document.kind}</span></div>
          <label className="replace-button">Remplacer<input type="file" onChange={(event) => replaceDocument(document.id, event.target.files[0])} /></label>
          <button type="button" className="delete-file" onClick={() => removeDocument(document.id)}>Supprimer</button>
        </div>)}
      </div>
      <label className="upload-zone"><Upload size={24} /><strong>Ajouter de nouvelles pièces</strong><span>PDF, images, WAV, MP3 ou M4A</span><input type="file" multiple onChange={(event) => addFiles(event.target.files)} /></label>
      {files.length > 0 && <div className="new-files"><strong>Nouveaux fichiers</strong>{Array.from(files).map((file, index) => <div key={`${file.name}-${index}`}><span>{file.name}</span><button type="button" onClick={() => setFiles((current) => Array.from(current).filter((_, itemIndex) => itemIndex !== index))}>Retirer</button></div>)}</div>}
      <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Annuler</button><button className="primary" disabled={busy || !changed}>{busy ? "Envoi..." : "Enregistrer et relancer"}</button></div>
    </form>
  </div>;
}

function ClaimModal({ form, setForm, files, setFiles, busy, onSubmit, onClose }) {
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  return <div className="modal-backdrop">
    <form className="modal" onSubmit={onSubmit}>
      <div className="modal-header"><div><span className="eyebrow">NOUVEAU DOSSIER</span><h2>Déclarer un sinistre</h2></div><button type="button" className="close" onClick={onClose}>×</button></div>
      <div className="form-grid">
        <label>Nom du client<input name="customer_name" value={form.customer_name} onChange={update} required /></label>
        <label>Numéro de contrat<input name="policy_number" value={form.policy_number} onChange={update} required /></label>
        <label>Date de l'accident<input type="date" name="incident_date" value={form.incident_date} onChange={update} required /></label>
        <label>Lieu<input name="location" value={form.location} onChange={update} required /></label>
      </div>
      <label>Description<textarea name="description" value={form.description} onChange={update} rows="4" placeholder="Exemple : une voiture m'a percuté à l'arrière..." required /></label>
      <label className="upload-zone"><Upload size={24} /><strong>Ajouter les pièces</strong><span>PDF, images et audio</span><input type="file" multiple onChange={(e) => setFiles(e.target.files)} /></label>
      {files.length > 0 && <p className="file-count">{files.length} fichier(s) sélectionné(s)</p>}
      <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Annuler</button><button className="primary" disabled={busy}>{busy ? "Envoi..." : "Lancer l'analyse"}</button></div>
    </form>
  </div>;
}

export default App;

