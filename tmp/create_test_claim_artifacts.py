from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT = Path(r"D:\5ds\deep\output\test-claim")
OUT.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

styles = getSampleStyleSheet()
body = ParagraphStyle("BodyFR", parent=styles["BodyText"], fontName="Arial", fontSize=10, leading=14, textColor=colors.HexColor("#27364B"))
small = ParagraphStyle("SmallFR", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#52617A"))
title = ParagraphStyle("TitleFR", parent=styles["Title"], fontName="Arial-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#0D4E9B"), spaceAfter=12)
heading = ParagraphStyle("HeadingFR", parent=styles["Heading2"], fontName="Arial-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#0D4E9B"), spaceBefore=10, spaceAfter=6)
center = ParagraphStyle("CenterFR", parent=body, alignment=TA_CENTER)
right = ParagraphStyle("RightFR", parent=body, alignment=TA_RIGHT)
table_header = ParagraphStyle("TableHeaderFR", parent=small, fontName="Arial-Bold", textColor=colors.white)

def p(text, style=body):
    return Paragraph(text, style)

def doc(path, story, title_text):
    def decorate(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7E2F0"))
        canvas.line(18*mm, 16*mm, 192*mm, 16*mm)
        canvas.setFont("Arial", 8)
        canvas.setFillColor(colors.HexColor("#6B778C"))
        canvas.drawString(18*mm, 10*mm, "Dossier synthétique de démonstration - ne constitue pas un document réel")
        canvas.drawRightString(192*mm, 10*mm, f"Page {document.page}")
        canvas.restoreState()
    pdf = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=22*mm, title=title_text, author="AI Claims Agent - Jeu de test")
    pdf.build(story, onFirstPage=decorate, onLaterPages=decorate)

def info_table(rows, widths=(48*mm, 120*mm)):
    data = [[p(f"<b>{k}</b>", small), p(v, body)] for k, v in rows]
    table = Table(data, colWidths=list(widths), hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EEF4FB")),
        ("BOX", (0,0), (-1,-1), 0.7, colors.HexColor("#B9CCE4")),
        ("INNERGRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D7E2F0")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return table

form = [p("FORMULAIRE DE DÉCLARATION DE SINISTRE", title), p("Référence dossier : CLM-2026-1012-0042", heading)]
form += [info_table([
    ("Assurée", "Inès Ben Salem"), ("Contrat", "AUTO-TN-2026-0042"),
    ("Véhicule", "Renault Clio blanche - immatriculation 214 TUN 8421"),
    ("Date et heure", "12/10/2026 à 17 h 40"), ("Lieu", "Avenue Habib Bourguiba, Tunis"),
    ("Type de sinistre", "Collision automobile - véhicule percuté à l'arrière"),
])]
form += [p("Déclaration", heading), p("Alors que je ralentissais devant un passage piéton, le véhicule qui me suivait n'a pas freiné à temps et a percuté l'arrière gauche de ma voiture. Le pare-chocs arrière est enfoncé et rayé, et le feu arrière gauche est légèrement fissuré. Aucun blessé n'est à signaler. Le véhicule reste roulant.")]
form += [p("Pièces jointes annoncées", heading), p("Constat amiable, trois photographies du véhicule, devis/facture estimative du garage et déclaration audio."), Spacer(1, 18*mm), p("Signature de l'assurée : Inès Ben Salem", right)]
doc(OUT / "01_formulaire_declaration.pdf", form, "Formulaire de déclaration")

report = [p("CONSTAT AMIABLE - SYNTHÈSE", title), p("Accident matériel sans blessé", center), Spacer(1, 4*mm)]
report += [info_table([
    ("Date", "12/10/2026"), ("Heure", "17 h 40"), ("Lieu", "Avenue Habib Bourguiba, Tunis"),
    ("Véhicule A", "Renault Clio blanche - 214 TUN 8421 - assurée : Inès Ben Salem"),
    ("Véhicule B", "Citadine grise - conducteur : Mohamed Trabelsi"),
    ("Blessés", "Non"), ("Dégâts autres que véhicules", "Non"),
])]
report += [p("Circonstances cochées", heading), info_table([
    ("Véhicule A", "Ralentissait / était arrêté devant un passage piéton"),
    ("Véhicule B", "Heurtait à l'arrière un véhicule roulant dans le même sens"),
])]
report += [p("Observations", heading), p("Le véhicule B a percuté l'arrière gauche du véhicule A à faible vitesse. Les dommages visibles sur le véhicule A concernent principalement le pare-chocs arrière gauche et le bloc optique arrière gauche. Les deux conducteurs déclarent être d'accord sur ces circonstances."), p("Croquis descriptif", heading)]
sketch = Table([[p("Véhicule B  →  [impact]  →  Véhicule A<br/><br/>Même voie - même sens de circulation", center)]], colWidths=[168*mm], rowHeights=[35*mm])
sketch.setStyle(TableStyle([("BOX",(0,0),(-1,-1),1,colors.HexColor("#7895B8")),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F7FAFE")),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
signatures = Table([[p("Signature conducteur A<br/><b>Inès Ben Salem</b>", small), p("Signature conducteur B<br/><b>Mohamed Trabelsi</b>", small)]], colWidths=[84*mm, 84*mm])
signatures.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LINEABOVE", (0,0), (-1,0), 0.5, colors.HexColor("#B9CCE4")), ("TOPPADDING", (0,0), (-1,-1), 7)]))
report += [sketch, Spacer(1, 12*mm), signatures]
doc(OUT / "02_constat_amiable.pdf", report, "Constat amiable synthétique")

invoice = [p("GARAGE CARROSSERIE EL AMEN", title), p("DEVIS DE RÉPARATION N° DEV-261014-118", heading)]
invoice += [info_table([
    ("Client", "Inès Ben Salem"), ("Véhicule", "Renault Clio blanche - 214 TUN 8421"),
    ("Contrat associé", "AUTO-TN-2026-0042"), ("Date du devis", "14/10/2026"),
    ("Objet", "Réparation des dommages consécutifs au choc arrière du 12/10/2026"),
])]
items = [
    [p("Désignation", table_header), p("Qté", table_header), p("P.U. HT", table_header), p("Total HT", table_header)],
    [p("Remplacement pare-chocs arrière"), p("1", center), p("980,000 TND", right), p("980,000 TND", right)],
    [p("Bloc optique arrière gauche"), p("1", center), p("420,000 TND", right), p("420,000 TND", right)],
    [p("Peinture et consommables"), p("1", center), p("380,000 TND", right), p("380,000 TND", right)],
    [p("Main-d'œuvre carrosserie (8 h)"), p("8", center), p("50,000 TND", right), p("400,000 TND", right)],
]
t = Table(items, colWidths=[86*mm, 18*mm, 32*mm, 32*mm], repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0D4E9B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("BOX",(0,0),(-1,-1),0.8,colors.HexColor("#9EB6D2")),("INNERGRID",(0,0),(-1,-1),0.4,colors.HexColor("#D7E2F0")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
invoice += [Spacer(1, 7*mm), t, Spacer(1, 6*mm)]
totals = Table([[p("Total HT", right), p("2 180,000 TND", right)], [p("TVA et taxes", right), p("300,000 TND", right)], [p("TOTAL TTC", right), p("2 480,000 TND", right)]], colWidths=[120*mm, 48*mm])
totals.setStyle(TableStyle([("FONTNAME",(0,-1),(-1,-1),"Arial-Bold"),("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#E6F0FC")),("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#B9CCE4")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
invoice += [totals, Spacer(1, 8*mm), p("Durée prévisionnelle : 4 jours ouvrés. Devis valable 30 jours. Ce document est synthétique et destiné uniquement aux tests du projet AI Claims Agent.", small)]
doc(OUT / "03_devis_reparation.pdf", invoice, "Devis de réparation synthétique")

print("\n".join(str(p) for p in sorted(OUT.glob("*.pdf"))))
