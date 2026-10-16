import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, Bot, BrainCircuit, Calculator, CheckCircle2, ChevronRight,
  Database, FileSearch, Gauge, GitBranch, Image, LayoutDashboard,
  LoaderCircle, Plus, RefreshCw, ShieldCheck, Upload, XCircle,
} from "lucide-react";
import { createClaim, getClaim, getSystemInfo, listClaims, retryClaim, updateClaimFiles } from "./api";

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
    getSystemInfo().then(setSystemInfo).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selected || !["SUBMITTED", "PROCESSING"].includes(selected.status)) return;
    const timer = setInterval(async () => {
      try {
        const updated = await getClaim(selected.id);
        setSelected(updated);
        setClaims((current) => current.map((item) => item.id === updated.id ? updated : item));
      } catch (err) {
        setError(err.message);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [selected?.id, selected?.status]);

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
            {selected ? <ClaimDetail claim={selected} onRetry={async () => setSelected(await retryClaim(selected.id))} onAddFiles={() => setSupplementClaim(selected)} /> : <div className="empty detail-empty"><Bot size={38} /><h3>Sélectionnez un dossier</h3><p>La décision et les preuves apparaîtront ici.</p></div>}
          </div>
        </section>
        </> : <TracePage systemInfo={systemInfo} claims={claims} selected={selected} setSelected={setSelected} />}
      </main>

      {showForm && <ClaimModal form={form} setForm={setForm} files={files} setFiles={setFiles} busy={busy} onSubmit={submit} onClose={() => setShowForm(false)} />}
      {supplementClaim && <SupplementModal claim={supplementClaim} files={supplementFiles} setFiles={setSupplementFiles} busy={busy} onSubmit={submitSupplement} onClose={() => { setSupplementClaim(null); setSupplementFiles([]); }} />}
    </div>
  );
}

function TracePage({ systemInfo, claims, selected, setSelected }) {
  const completed = selected?.status === "COMPLETED" ? selected : claims.find((item) => item.status === "COMPLETED");
  const results = completed?.agent_results || {};
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
        <select value={completed?.id || ""} onChange={(e) => setSelected(claims.find((item) => item.id === e.target.value))}>
          <option value="">Architecture générale</option>
          {claims.map((claim) => <option key={claim.id} value={claim.id}>{claim.customer_name} · {claim.status}</option>)}
        </select>
      </label>
      {completed && <div className="trace-summary"><span>Décision</span><strong>{completed.decision}</strong><span>Risque</span><strong>{completed.risk_score}/100</strong><span>Confiance</span><strong>{Math.round((completed.confidence || 0) * 100)}%</strong></div>}
    </section>

    <section className="timeline-section">
      <div className="trace-title"><GitBranch /><div><h2>Timeline des agents</h2><p>Les trois premiers agents s'exécutent en parallèle, puis leurs résultats sont fusionnés.</p></div></div>
      <div className="timeline">
        <div className="parallel-group">
          <span className="phase-label">Phase 1 · Parallèle</span>
          <div className="parallel-agents">{systemInfo.agents.filter((a) => a.order === 1).map((agent) => <AgentCard key={agent.key} agent={agent} result={results[agent.key]} />)}</div>
        </div>
        <div className="timeline-arrow">↓ Fusion des résultats</div>
        {systemInfo.agents.filter((a) => a.order > 1).map((agent) => <div key={agent.key} className="sequential-step"><span className="phase-label">Phase {agent.order} · Séquentielle</span><AgentCard agent={agent} result={agent.key === "decision" ? decisionResult : results[agent.key]} /></div>)}
      </div>
    </section>

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
        <div className="calculation-result"><Gauge /><div><span>Calcul de ce dossier</span>{fraud.score_breakdown?.length ? fraud.score_breakdown.map((item) => <p key={item.rule}>+{item.points} · {item.evidence}</p>) : <p>Aucune incohérence détectée : +0</p>}<strong>Total : {completed?.risk_score ?? 0}/100</strong></div></div>
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

function AgentCard({ agent, result }) {
  return <article className={`agent-card ${result ? "has-result" : ""}`}>
    <div className="agent-card-head"><span className="agent-icon"><Bot /></span><div><h3>{agent.name}</h3><span>{result ? "Exécuté" : agent.status}</span></div></div>
    <dl><div><dt>Moteur actuel</dt><dd>{agent.engine}</dd></div><div><dt>LLM</dt><dd>{agent.llm || "Aucun LLM dans le MVP"}</dd></div><div><dt>Entrée</dt><dd>{agent.input}</dd></div><div><dt>Sortie</dt><dd>{agent.output}</dd></div></dl>
    {result && <details><summary>Voir la sortie JSON</summary><pre>{JSON.stringify(result, null, 2)}</pre></details>}
  </article>;
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

function ClaimDetail({ claim, onRetry, onAddFiles }) {
  const info = decisionInfo[claim.decision];
  const Icon = info?.icon || LoaderCircle;
  return <div className="detail-content">
    <div className="detail-heading">
      <div><span className="claim-id">DOSSIER #{claim.id.slice(0, 8).toUpperCase()}</span><h2>{claim.customer_name}</h2><p>{claim.policy_number} · {claim.location}</p></div>
      <span className={`decision-badge ${info?.className || "processing"}`}><Icon className={claim.status === "PROCESSING" ? "spin" : ""} />{info?.label || statusLabels[claim.status]}</span>
    </div>
    <div className="description"><span>Déclaration</span><p>{claim.description}</p></div>
    {claim.status === "FAILED" && <div className="failure"><p>{claim.error_message}</p><button className="secondary" onClick={onRetry}>Relancer n8n</button></div>}
    {["SUBMITTED", "PROCESSING"].includes(claim.status) && <div className="processing-card"><LoaderCircle className="spin" /><div><strong>Analyse automatique en cours</strong><p>n8n coordonne les agents spécialisés.</p></div></div>}
    {claim.status === "COMPLETED" && <>
      <div className="score-grid"><div><span>Confiance</span><strong>{Math.round((claim.confidence || 0) * 100)}%</strong></div><div><span>Score de risque</span><strong>{claim.risk_score ?? 0}/100</strong></div><div><span>Documents</span><strong>{claim.documents.length}</strong></div></div>
      <section className="evidence"><h3>Justification</h3>{claim.reasons.map((reason, index) => <p key={index}><CheckCircle2 size={17} />{reason}</p>)}</section>
      <section className="evidence"><h3>Références du contrat</h3>{claim.policy_references.length ? claim.policy_references.map((ref, index) => <p key={index}><ShieldCheck size={17} />Page {ref.page || "?"} · {ref.section || ref.source} · {ref.text}</p>) : <p>Aucune référence retournée.</p>}</section>
    </>}
    {["COMPLETED", "FAILED"].includes(claim.status) && <div className="detail-actions"><button className="primary" onClick={onAddFiles}><Upload size={17} />Gérer les pièces et relancer</button></div>}
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

