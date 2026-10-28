from pathlib import Path
import textwrap


OUT = Path(r"D:\5ds\deep\output\pdf\dossier-demo-refus-france")
OUT.mkdir(parents=True, exist_ok=True)


def pdf_escape(text):
    return text.encode("cp1252", errors="replace").hex().upper()


def make_pdf(filename, title, lines):
    all_lines = [title, ""]
    for line in lines:
        all_lines.extend(textwrap.wrap(line, width=88, break_long_words=False) or [""])
        all_lines.append("")

    commands = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate(all_lines):
        if index == 0:
            commands.append("/F1 15 Tf")
            commands.append(f"<{pdf_escape(line)}> Tj")
            commands.append("/F1 10 Tf")
        else:
            commands.append(f"<{pdf_escape(line)}> Tj")
        commands.append("T*")
    commands.extend(["ET", "BT", "/F1 8 Tf", "50 28 Td", f"<{pdf_escape('DOSSIER SYNTHÉTIQUE DE TEST — SANS VALEUR JURIDIQUE')}> Tj", "ET"])
    stream = "\n".join(commands).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode("ascii"))
        data.extend(obj)
        data.extend(b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    (OUT / filename).write_bytes(data)


name = "Camille Laurent"
policy = "AXA-FR-DEMO-2026-0151"
vehicle = "Peugeot 208 bleu nuit, immatriculation fictive FV-317-XM"
date = "26 octobre 2026 à 11 h 20"
place = "Circuit d'essais fictif du Val de Saône, France"
incident = (
    "Pendant une session d'essais chronométrés sur circuit fermé, un contact à faible vitesse "
    "a endommagé l'avant gauche de ma Peugeot 208 : pare-chocs avant gauche enfoncé et feu "
    "avant gauche fissuré. Aucun blessé. Le véhicule est resté roulant."
)

make_pdf("01_formulaire_declaration.pdf", "FORMULAIRE DE DECLARATION DE SINISTRE", [
    "Assurée : Camille Laurent",
    f"Contrat : {policy}",
    f"Véhicule : {vehicle}",
    f"Date et heure : {date}",
    f"Lieu : {place}",
    "Type de sinistre : dommages matériels au véhicule assuré.",
    f"Déclaration de l'assurée : {incident}",
    "La conductrice confirme qu'elle pilotait le véhicule pendant les essais chronométrés de l'événement automobile amateur Défi Circuit Démo 2026.",
    "Aucun tiers n'a été blessé. Le véhicule a été transporté au paddock puis au garage.",
    "Signature : Camille Laurent (nom et signature fictifs, dossier de démonstration).",
])

make_pdf("02_constat_incident_circuit.pdf", "CONSTAT D'INCIDENT — CIRCUIT FERME", [
    "Référence fictive : EVT-26-1026-051",
    f"Conductrice : {name} — contrat déclaré : {policy}",
    f"Véhicule assuré : {vehicle}",
    f"Date et heure : {date}",
    f"Lieu : {place}",
    "Événement : Défi Circuit Démo 2026 — série amateur, session d'essais chronométrés.",
    "Circonstances consignées par l'organisateur : lors d'un essai chronométré sur la piste fermée, le véhicule a touché un élément de balisage dans un virage. Aucun véhicule tiers n'est impliqué.",
    "Dommages constatés : pare-chocs avant gauche enfoncé et feu avant gauche fissuré. Aucun blessé.",
    "Le véhicule a été immobilisé dans le paddock après l'incident.",
    "Document fictif produit uniquement pour tester le traitement automatique d'un cas exclu.",
])

make_pdf("03_conditions_particulieres_AXA_DEMO_EXCLUSION.pdf", "CONDITIONS PARTICULIERES — CONTRAT DE DEMONSTRATION", [
    "Document entièrement fictif, sans lien avec AXA et sans valeur juridique.",
    f"Assurée : {name}",
    f"Numéro de contrat : {policy}",
    f"Véhicule assuré : {vehicle}",
    "Période de démonstration : du 1er janvier 2026 au 31 décembre 2026.",
    "Garantie dommages tous accidents : souscrite et active pendant la période indiquée.",
    "FRANCHISE : 300 EUR par sinistre garanti.",
    "EXCLUSION EXPLICITE — COURSES ET COMPETITIONS AUTOMOBILES : ne sont pas garantis les dommages survenus lorsque le véhicule participe à une compétition, une course, des essais chronométrés ou un entraînement sur circuit automobile, y compris sur circuit fermé et même en l'absence de tiers impliqué.",
    "Application au présent contrat : cette exclusion s'applique aux essais chronométrés mentionnés dans le constat d'incident EVT-26-1026-051 du 26 octobre 2026.",
    "Les autres conditions générales ne peuvent pas annuler cette exclusion particulière dans ce cas de démonstration.",
])

make_pdf("04_devis_reparation.pdf", "DEVIS DE REPARATION — GARAGE DEMO LYON", [
    "Devis fictif : GD-2026-1048 — date : 27 octobre 2026.",
    f"Cliente : {name}",
    f"Véhicule : {vehicle}",
    f"Contrat associé : {policy}",
    "Remplacement du pare-chocs avant : 920 EUR TTC.",
    "Remplacement du feu avant gauche : 460 EUR TTC.",
    "Peinture et consommables : 310 EUR TTC.",
    "Main-d'oeuvre carrosserie : 520 EUR TTC.",
    "TOTAL TTC : 2 210 EUR.",
    "Le devis ne préjuge pas de la prise en charge par l'assureur.",
    "Document fictif pour test logiciel uniquement.",
])

(OUT / "README_TEST.txt").write_text(
    "DOSSIER DE TEST FICTIF — RESULTAT CIBLE : REFUSE (REJECT)\n\n"
    "Tous les noms, le contrat, le véhicule, l'événement, le constat et le devis sont inventés. "
    "Le contrat de démonstration ne provient pas d'AXA et n'a aucune valeur juridique.\n\n"
    "A saisir dans le site :\n"
    f"Nom : {name}\nContrat : {policy}\nDate : 26/10/2026\n"
    f"Lieu : {place}\nDescription : {incident}\n\n"
    "Joindre les 4 PDF de ce dossier. Le document 03 porte une exclusion explicite qui vise "
    "les essais chronométrés sur circuit fermé. La déclaration et le constat indiquent exactement "
    "ce contexte. La décision cible est REJECT car l'exclusion contractuelle correspond au sinistre.\n\n"
    "Si l'application ne renvoie pas REJECT, consulter les résultats du Policy RAG : le modèle local "
    "peut encore mal interpréter une clause. Ce jeu de test sert à mesurer cette limite; il ne décrit "
    "pas une vraie décision d'assurance.\n",
    encoding="utf-8",
)

print(OUT)
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size)
