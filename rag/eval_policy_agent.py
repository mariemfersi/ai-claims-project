"""Évaluation de bout en bout du Policy Agent sur les dossiers synthétiques.

Usage :
    python rag/eval_policy_agent.py                       # avec reformulation (2 appels Gemini par dossier)
    python rag/eval_policy_agent.py --sans-reformulation  # 1 appel par dossier
    python rag/eval_policy_agent.py --sans-cache          # nouveaux appels même si les réponses sont en cache
    python rag/eval_policy_agent.py --reecrire            # écrase les résultats même si tout vient du cache
    python rag/eval_policy_agent.py --dossiers D01 D02

Pour chaque dossier (conditions particulières depuis contrat_reference, intake construit
par policy_agent.intake_depuis_dossier), compare la sortie de analyse_couverture avec
« attendu » :
- rappel des articles : part des articles attendus présents dans articles_cites ;
- précision des articles : part des articles cités qui sont attendus ;
- rappel des articles fournis : part des articles attendus parmi les articles fournis au
  LLM, pour séparer les erreurs de retrieval des erreurs de raisonnement ;
- rappel « périmètre couverture » : le rappel sans les articles de procédure et de fraude
  (18, 19, 23, 24, 25, 26), que les sous-questions de couverture ne visent pas ;
- verdict : accept ↔ couvert, reject ↔ non_couvert, investigate ↔ partiel ou indetermine.

Avant de lancer, affiche le nombre d'appels Gemini prévus hors cache (sans compter les
nouveaux essais après une erreur 503). Si le quota est épuisé, s'arrête proprement :
les résultats déjà obtenus sont écrits (results/eval_policy_agent[_sans_reformulation].md
et .json), et les réponses déjà reçues restent dans le cache pour la reprise.

Une relance dont toutes les réponses viennent du cache n'écrase pas les fichiers de résultats
existants (ils décrivent le lancement d'origine : date, appels réseau) ; elle affiche seulement
les résultats. --reecrire force l'écriture.
"""
import argparse, json, time
from pathlib import Path
import policy_agent as pa

ROOT = Path(__file__).resolve().parent.parent
DECISION_VERDICTS = {"accept": {"couvert"}, "reject": {"non_couvert"}, "investigate": {"partiel", "indetermine"}}
# contrat, articles 18 à 26 : pièces, expertise, fraude, procédures internes (Fraud / Decision Agents)
HORS_PERIMETRE = {"18", "19", "23", "24", "25", "26"}


def appels_prevus(dossiers, cp, reformulation):
    """Nombre d'appels Gemini hors cache, sans appeler l'API : la reformulation est relue dans
    le cache quand elle y est, ce qui permet de reconstruire le prompt P4 et de vérifier le sien."""
    total, detail = 0, {}
    for d in dossiers:
        intake = pa.intake_depuis_dossier(d, cp)
        questions = pa.sous_questions(intake)
        n = 0
        if reformulation:
            if not pa.cache_path(pa.PROMPT_R1, pa.message_r1(questions)).exists():
                detail[d["id"]] = 2  # reformulation + P4 (prompt P4 inconnu tant que la reformulation manque)
                total += 2
                continue
            questions = pa.reformuler(questions, [], [], {"quota_epuise": False})  # lu dans le cache
        user, _ = pa.prompt_p4(intake, pa.retrouver_articles(questions))
        n += not pa.cache_path(pa.PROMPT_P4, user).exists()
        detail[d["id"]] = n
        total += n
    return total, detail


def mesurer(d, res):
    attendu = d["attendu"]
    erreurs_appel = [c["statut"] for c in res["trace"]["appels"] if c["statut"] not in ("ok", "cache")]
    appels = {"cache": sum(c["statut"] == "cache" for c in res["trace"]["appels"]),
              "reseau": sum(c["statut"] != "cache" for c in res["trace"]["appels"]), "erreurs": erreurs_appel}
    fournis = [a["article"] for a in res["trace"]["articles_fournis"]]
    if res["justification"].startswith("Analyse impossible"):
        # pas de réponse P4 : ni le retrieval ni le raisonnement ne sont en cause, dossier exclu des métriques
        return {"id": d["id"], "scenario": d["scenario"], "decision_attendue": attendu["decision"],
                "erreur_appel": True, "verdict": "—", "verdict_ok": None, "confiance": "—",
                "attendus": sorted(attendu["articles"]), "cites": [], "fournis": fournis,
                "rappel": None, "precision": None, "rappel_perimetre": None, "cites_non_attendus": [],
                "rappel_fournis": len(set(attendu["articles"]) & set(fournis)) / len(attendu["articles"]),
                "appels": appels, "justification": res["justification"],
                "causes": [f"pas de réponse P4 ({res['justification']}) : erreur d'appel, dossier exclu des "
                           "métriques de raisonnement"]}
    exp = set(attendu["articles"])
    cites = res["articles_cites"]
    ok_cites, ok_fournis = exp & set(cites), exp & set(fournis)
    perimetre = exp - HORS_PERIMETRE
    verdict_ok = res["verdict_couverture"] in DECISION_VERDICTS[attendu["decision"]]
    causes = []
    for a in sorted(exp - set(cites)):
        hors = " (hors périmètre couverture)" if a in HORS_PERIMETRE else ""
        if a not in fournis:
            causes.append(f"article {a} absent des articles fournis : retrieval{hors}")
        else:
            causes.append(f"article {a} fourni mais non cité : raisonnement{hors}")
    if not verdict_ok:
        causes.append(f"verdict « {res['verdict_couverture']} » au lieu de "
                      f"{' ou '.join(sorted(DECISION_VERDICTS[attendu['decision']]))} : raisonnement")
    return {"id": d["id"], "scenario": d["scenario"], "decision_attendue": attendu["decision"],
            "erreur_appel": False, "verdict": res["verdict_couverture"], "verdict_ok": verdict_ok, "confiance": res["confiance"],
            "attendus": sorted(exp), "cites": cites, "fournis": fournis,
            "rappel": len(ok_cites) / len(exp),
            "precision": len(ok_cites) / len(cites) if cites else None,
            "rappel_fournis": len(ok_fournis) / len(exp),
            "rappel_perimetre": len(perimetre & set(cites)) / len(perimetre) if perimetre else None,
            "cites_non_attendus": [a for a in cites if a not in exp],
            "appels": appels, "justification": res["justification"], "causes": causes}


def moyenne(lignes, champ):
    vals = [l[champ] for l in lignes if l[champ] is not None]
    return sum(vals) / len(vals) if vals else None


def pct(x):
    return "—" if x is None else f"{100 * x:.0f} %"


def rapport(lignes, meta):
    out = ["# Évaluation de bout en bout du Policy Agent", "",
           f"- Date : {meta['date']} ; modèle : `{meta['modele']}` ; reasoning_effort : `{meta['effort']}` ; "
           f"reformulation : {'oui' if meta['reformulation'] else 'non'}.",
           f"- Dossiers évalués : {len(lignes)} sur {meta['total']}"
           + (f" (**arrêt : quota Gemini épuisé avant {meta['arret']}**)." if meta["arret"] else "."),
           "- Intake : construit par `intake_depuis_dossier` (résumés courts rédigés à la main au format P1, "
           "en attendant la vraie sortie de P1) ; conditions particulières : `contrat_reference`.",
           "- Verdict attendu : accept → couvert ; reject → non_couvert ; investigate → partiel ou indetermine.",
           "- « Périmètre couverture » : rappel sans les articles 18, 19, 23, 24, 25, 26 (pièces, expertise, "
           "fraude, procédures internes), que les sous-questions de couverture ne visent pas ; ils relèvent "
           "des agents Fraud et Decision.", "",
           "## Résultats par dossier", "",
           "| Dossier | Attendu | Verdict | Verdict OK | Articles attendus | Fournis | Cités | Rappel (complet) "
           "| Rappel (périmètre couverture) | Précision | Rappel fournis | Confiance | Appels (cache / réseau) |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in lignes:
        fournis = ", ".join(f"**{a}**" if a in l["attendus"] else a for a in l["fournis"])
        ok = "erreur d'appel" if l["erreur_appel"] else ("oui" if l["verdict_ok"] else "**non**")
        out.append(f"| {l['id']} | {l['decision_attendue']} | {l['verdict']} | {ok} "
                   f"| {', '.join(l['attendus'])} | {fournis} | {', '.join(l['cites']) or '—'} | {pct(l['rappel'])} "
                   f"| {pct(l['rappel_perimetre'])} | {pct(l['precision'])} | {pct(l['rappel_fournis'])} "
                   f"| {l['confiance']} | {l['appels']['cache']} / {l['appels']['reseau']} |")
    repondus = [l for l in lignes if not l["erreur_appel"]]
    out += ["", "Dans la colonne « Fournis », les articles attendus sont en gras.", "", "## Moyennes", "",
            f"Sur les {len(repondus)} dossiers avec une réponse P4 ({len(lignes) - len(repondus)} erreur(s) d'appel "
            "exclue(s), sauf pour le rappel des articles fournis, mesuré avant l'appel P4).", "",
            "| Métrique | Valeur |", "|---|---|",
            f"| Verdict cohérent | {sum(l['verdict_ok'] for l in repondus)} / {len(repondus)} |",
            f"| Rappel des articles cités, complet | {pct(moyenne(lignes, 'rappel'))} |",
            f"| Rappel des articles cités, périmètre couverture | {pct(moyenne(lignes, 'rappel_perimetre'))} |",
            f"| Précision des articles (dossiers avec au moins un article cité) | {pct(moyenne(lignes, 'precision'))} |",
            f"| Rappel des articles fournis au LLM | {pct(moyenne(lignes, 'rappel_fournis'))} |",
            "", "Le rappel **complet** compte tous les articles attendus du dossier ; le rappel **périmètre "
            "couverture** ne compte que ceux qui relèvent de l'analyse de couverture, sans les articles 18, 19, 23, "
            "24, 25 et 26 (pièces, expertise, fraude, procédures internes), qui relèvent des agents Fraud et "
            "Decision. Un écart entre les deux vient de ces articles hors périmètre, pas d'une erreur du Policy "
            "Agent. Un dossier dont tous les articles attendus sont hors périmètre n'a pas de rappel périmètre "
            "(« — ») et n'entre pas dans sa moyenne.", "", "## Échecs et cause", ""]
    for l in lignes:
        if l["causes"]:
            out.append(f"- **{l['id']}** ({l['scenario']}) :")
            out += [f"  - {c}" for c in l["causes"]]
            if l["cites_non_attendus"]:
                out.append(f"  - cités sans être attendus : {', '.join(l['cites_non_attendus'])}")
    out += ["", f"Avec {len(lignes)} dossiers, un dossier représente {pct(1 / len(lignes)) if lignes else '—'} "
            "du verdict : ces chiffres décrivent ce jeu de test, pas une performance générale.", ""]
    return "\n".join(out)


def ecrire(suffixe, lignes, meta):
    """Écrit le JSON et le rapport ; une section « ## Analyse » rédigée à la main dans le rapport
    existant est conservée à la fin (à relire si les résultats ont changé)."""
    md = ROOT / f"results/eval_policy_agent{suffixe}.md"
    analyse = ""
    if md.exists() and "\n## Analyse" in md.read_text(encoding="utf-8"):
        analyse = md.read_text(encoding="utf-8").split("\n## Analyse", 1)[1]
        analyse = f"\n## Analyse{analyse}"
    (ROOT / f"results/eval_policy_agent{suffixe}.json").write_text(
        json.dumps({"meta": meta, "dossiers": lignes}, ensure_ascii=False, indent=1), encoding="utf-8")
    md.write_text(rapport(lignes, meta) + analyse, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dossiers", nargs="*", help="identifiants (par défaut : tous)")
    ap.add_argument("--sans-reformulation", action="store_true")
    ap.add_argument("--sans-cache", action="store_true")
    ap.add_argument("--reecrire", action="store_true",
                    help="écrase les résultats existants même si toutes les réponses viennent du cache")
    args = ap.parse_args()
    reformulation = not args.sans_reformulation

    data = json.loads((ROOT / "data/dossiers/dossiers_synthetiques.json").read_text(encoding="utf-8"))
    cp = data["contrat_reference"]
    dossiers = [d for d in data["dossiers"] if not args.dossiers or d["id"] in args.dossiers]
    if args.sans_cache:
        prevus = len(dossiers) * (2 if reformulation else 1)
        print(f"Appels Gemini prévus : {prevus} (--sans-cache)")
    else:
        prevus, detail = appels_prevus(dossiers, cp, reformulation)
        print(f"Appels Gemini prévus hors cache : {prevus} "
              f"({', '.join(f'{k} : {v}' for k, v in detail.items())}), sans compter les nouveaux essais")

    suffixe = "" if reformulation else "_sans_reformulation"
    meta = {"date": time.strftime("%Y-%m-%d %H:%M"), "modele": pa.os.environ.get("GEMINI_MODEL", pa.DEFAULT_MODEL),
            "effort": pa.os.environ.get("GEMINI_REASONING_EFFORT", "low") or "non envoyé",
            "reformulation": reformulation, "total": len(dossiers), "arret": None}
    existants = [p for p in (ROOT / f"results/eval_policy_agent{suffixe}.md", ROOT / f"results/eval_policy_agent{suffixe}.json")
                 if p.exists()]
    # relance entièrement depuis le cache : les fichiers existants décrivent le lancement d'origine
    proteger = not args.sans_cache and prevus == 0 and bool(existants) and not args.reecrire
    if proteger:
        print("Toutes les réponses sont en cache : les résultats existants ne seront pas écrasés "
              "(--reecrire pour les remplacer).")
    lignes = []
    for d in dossiers:
        res = pa.analyse_couverture(pa.intake_depuis_dossier(d, cp), cache=not args.sans_cache,
                                    reformulation=reformulation)
        if res["trace"]["quota_epuise"]:
            meta["arret"] = d["id"]
            print(f"{d['id']} : quota Gemini épuisé, arrêt ({len(lignes)} dossiers évalués)")
            break
        lignes.append(mesurer(d, res))
        l = lignes[-1]
        etat = "erreur d'appel" if l["erreur_appel"] else ("OK" if l["verdict_ok"] else "KO")
        print(f"{d['id']} : {l['verdict']} (attendu {l['decision_attendue']}, {etat}) "
              f"rappel {pct(l['rappel'])}, fournis {pct(l['rappel_fournis'])}, appels {l['appels']}")
        if proteger and l["appels"]["reseau"]:
            proteger = False  # imprévu (cache supprimé entre-temps ?) : de nouvelles réponses, on les écrit
            print("Appel réseau inattendu : les résultats seront écrits.")
        if not proteger:
            ecrire(suffixe, lignes, meta)  # après chaque dossier : rien n'est perdu en cas d'arrêt
    if meta["arret"] and lignes and not proteger:
        ecrire(suffixe, lignes, meta)
    if proteger:
        print(f"Résultats non écrits ; fichiers existants conservés : "
              f"{', '.join(str(p.relative_to(ROOT)) for p in existants)}")
    else:
        print(f"Résultats : results/eval_policy_agent{suffixe}.md")


if __name__ == "__main__":
    main()
