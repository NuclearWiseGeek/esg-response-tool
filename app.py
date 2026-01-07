import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from datetime import datetime
from dataclasses import dataclass

# --- 1. TRANSLATION ENGINE (The Dictionary Brain) ---
TRANSLATIONS = {
    "en": {
        "title": "🏢 Supplier ESG Enterprise OS",
        "caption": "Aligned with GHG Protocol (Scope 1, 2 & Grey Fleet)",
        "sidebar_lang": "Language / Langue",
        "step1_header": "Step 1: Company Profile",
        "company_label": "Company Legal Name",
        "country_label": "Site Country",
        "country_default": "France",
        "year_label": "Reporting Period",
        "revenue_label": "Annual Revenue",
        "currency_label": "Currency",
        "btn_start": "Start Assessment",
        "err_company": "Company Name and Revenue are required.",
        
        "step2_header": "Step 2: Activity Data",
        "s1_header": "🔥 Scope 1: Direct Emissions",
        "s1_stat": "**Stationary Combustion**",
        "gas_label": "Natural Gas (kWh)",
        "oil_label": "Heating Oil (Liters)",
        "propane_label": "Propane (kg)",
        "s1_mobile": "**Mobile Combustion (Company Fleet)**",
        "diesel_label": "Fleet Diesel (Liters)",
        "petrol_label": "Fleet Petrol (Liters)",
        "s1_fugitive": "**Fugitive Emissions (Refrigerants)**",
        "r410a_label": "R410A Refill (kg)",
        "r32_label": "R32 Refill (kg)",
        "r134a_label": "R134a Refill (kg)",
        "s2_header": "⚡ Scope 2: Indirect Energy",
        "elec_label": "Electricity (kWh)",
        "heat_label": "District Heating (kWh)",
        "s3_header": "🚗 Scope 3: Grey Fleet",
        "s3_desc": "Business travel in employee-owned vehicles.",
        "grey_label": "Total Distance (km)",
        "upload_label": "Upload Evidence",
        "signer_label": "Full Legal Name of Authorized Signer (e.g. Jean Dupont)",
        "btn_gen": "Generate Report",
        "err_signer": "Please enter a valid full name for the attestation signature.",
        
        "step3_header": "Step 3: Validated",
        "total_footprint": "Total Footprint",
        "btn_download": "Download Corporate Carbon Pack (PDF)",
        "btn_new": "New Assessment",
        
        # PDF Content
        "pdf_title": "CORPORATE CARBON FOOTPRINT DECLARATION",
        "pdf_method": "Methodology Aligned with GHG Protocol & ISO 14064-1",
        "pdf_date": "Date:",
        "pdf_company": "Company Name:",
        "pdf_country": "Site Country:",
        "pdf_period": "Reporting Period:",
        "pdf_revenue": "Annual Revenue:",
        "pdf_boundary_title": "BOUNDARY STATEMENT:",
        "pdf_boundary_text": """
        This report covers <b>Scope 1</b> (Direct), <b>Scope 2</b> (Energy Indirect), and selected <b>Scope 3</b> 
        (Grey Fleet / Business Travel). Excludes upstream/downstream Scope 3 categories unless noted.
        Calculations use <b>ADEME Base Carbone</b> emission factors.
        """,
        "pdf_summary_title": "EMISSIONS SUMMARY",
        "pdf_col_metric": "METRIC",
        "pdf_col_value": "VALUE",
        "pdf_s1": "Scope 1 (Direct Emissions)",
        "pdf_s2": "Scope 2 (Indirect Energy)",
        "pdf_s3": "Scope 3 (Grey Fleet)",
        "pdf_total": "TOTAL FOOTPRINT",
        "pdf_intensity": "CARBON INTENSITY",
        "pdf_detail_title": "Detailed Breakdown:",
        "pdf_tab_scope": "Scope",
        "pdf_tab_act": "Activity",
        "pdf_tab_qty": "Qty",
        "pdf_tab_emi": "Emissions (kg)",
        
        "pdf_evidence_title": "Evidence & Assurance:",
        "pdf_assurance_level": "<b>Assurance Level:</b> Limited (self-attested, document trail available)",
        "pdf_doc_retained": "<b>Supporting documentation retained by supplier:</b>",
        "pdf_no_mat": "No material emissions reported.",
        "pdf_avail": "Available upon buyer request",
        "pdf_attached": "digital files attached",
        "pdf_no_files": "No digital files attached",
        
        "pdf_attest_title": "ATTESTATION:",
        "pdf_attest_text": "I, <b>{signer}</b>, certify that the activity data and revenue provided are accurate to the best of my knowledge.",
        "pdf_sig": "Authorized Signature",
        
        "pdf_disc_title": "DISCLAIMER:",
        "pdf_disc_main": "This report uses supplier-provided data and ADEME Base Carbone factors. It has not been independently verified.",
        "pdf_exclusion_intro": "<b>Boundary Exclusions:</b> The following sources were assessed but excluded due to zero reported activity:",
        "pdf_exclusion_none": "<b>Boundary Exclusions:</b> None (All standard boundary categories were reported).",
        "pdf_disc_verify": "Buyers should conduct due diligence for CSRD reporting. For third-party verification: <b>verify@vsme.io</b>",
        
        "footer_l1": "Generated by VSME Supplier ESG OS",
        "footer_l2": "Aligned with GHG Protocol & ISO 14064-1 quantification methodologies.",
        "footer_l3": "Supports CSRD ESRS E1 quantitative reporting requirements.",
        "footer_l4": "Emission Factors: ADEME Base Carbone v23.0 (France)",
        
        # Evidence Labels
        "ev_gas": "Natural Gas Invoices",
        "ev_oil": "Heating Oil Purchase Receipts",
        "ev_prop": "Propane Purchase Receipts",
        "ev_diesel": "Fuel Logs/Receipts (Diesel)",
        "ev_petrol": "Fuel Logs/Receipts (Petrol)",
        "ev_hvac": "HVAC Maintenance Log (Refrigerants)",
        "ev_elec": "Electricity Utility Invoices",
        "ev_heat": "District Heating Invoices",
        "ev_travel": "Mileage Claims / Travel Logs"
    },
    
    "fr": {
        "title": "🏢 VSME Enterprise OS (RSE Fournisseur)",
        "caption": "Aligné avec le GHG Protocol (Scope 1, 2 & Déplacements Pro)",
        "sidebar_lang": "Langue / Language",
        "step1_header": "Étape 1 : Profil de l'Entreprise",
        "company_label": "Raison Sociale",
        "country_label": "Pays du Site",
        "country_default": "France",
        "year_label": "Période de Reporting",
        "revenue_label": "Chiffre d'Affaires Annuel",
        "currency_label": "Devise",
        "btn_start": "Commencer l'évaluation",
        "err_company": "Le nom de l'entreprise et le CA sont requis.",
        
        "step2_header": "Étape 2 : Données d'Activité",
        "s1_header": "🔥 Scope 1 : Émissions Directes",
        "s1_stat": "**Combustion Stationnaire**",
        "gas_label": "Gaz Naturel (kWh)",
        "oil_label": "Fioul Domestique (Litres)",
        "propane_label": "Propane (kg)",
        "s1_mobile": "**Combustion Mobile (Flotte Entreprise)**",
        "diesel_label": "Diesel Flotte (Litres)",
        "petrol_label": "Essence Flotte (Litres)",
        "s1_fugitive": "**Émissions Fugitives (Frigorifiques)**",
        "r410a_label": "Recharge R410A (kg)",
        "r32_label": "Recharge R32 (kg)",
        "r134a_label": "Recharge R134a (kg)",
        "s2_header": "⚡ Scope 2 : Énergie Indirecte",
        "elec_label": "Électricité (kWh)",
        "heat_label": "Chauffage Urbain (kWh)",
        "s3_header": "🚗 Scope 3 : Déplacements Pro",
        "s3_desc": "Déplacements professionnels (véhicules personnels / Grey Fleet).",
        "grey_label": "Distance Totale (km)",
        "upload_label": "Télécharger Justificatifs",
        "signer_label": "Nom complet du signataire autorisé (ex: Jean Dupont)",
        "btn_gen": "Générer le Rapport",
        "err_signer": "Veuillez entrer un nom valide pour la signature.",
        
        "step3_header": "Étape 3 : Validation",
        "total_footprint": "Empreinte Totale",
        "btn_download": "Télécharger le Pack Carbone (PDF)",
        "btn_new": "Nouvelle Évaluation",
        
        # PDF Content
        "pdf_title": "DÉCLARATION D'EMPREINTE CARBONE",
        "pdf_method": "Méthodologie alignée avec GHG Protocol & ISO 14064-1",
        "pdf_date": "Date :",
        "pdf_company": "Entreprise :",
        "pdf_country": "Pays du Site :",
        "pdf_period": "Période :",
        "pdf_revenue": "Chiffre d'Affaires :",
        "pdf_boundary_title": "DÉCLARATION DE PÉRIMÈTRE :",
        "pdf_boundary_text": """
        Ce rapport couvre le <b>Scope 1</b> (Direct), le <b>Scope 2</b> (Énergie Indirecte), et une partie du <b>Scope 3</b> 
        (Déplacements Professionnels). Exclut les catégories amont/aval du Scope 3 sauf indication contraire.
        Calculs basés sur les facteurs d'émission <b>ADEME Base Carbone</b>.
        """,
        "pdf_summary_title": "RÉSUMÉ DES ÉMISSIONS",
        "pdf_col_metric": "MÉTRIQUE",
        "pdf_col_value": "VALEUR",
        "pdf_s1": "Scope 1 (Émissions Directes)",
        "pdf_s2": "Scope 2 (Énergie Indirecte)",
        "pdf_s3": "Scope 3 (Déplacements Pro)",
        "pdf_total": "EMPREINTE TOTALE",
        "pdf_intensity": "INTENSITÉ CARBONE",
        "pdf_detail_title": "Détail des Calculs :",
        "pdf_tab_scope": "Scope",
        "pdf_tab_act": "Activité",
        "pdf_tab_qty": "Qté",
        "pdf_tab_emi": "Émissions (kg)",
        
        "pdf_evidence_title": "Preuves & Assurance :",
        "pdf_assurance_level": "<b>Niveau d'Assurance :</b> Limité (auto-déclaratif, traçabilité documentaire disponible)",
        "pdf_doc_retained": "<b>Documentation justificative conservée par le fournisseur :</b>",
        "pdf_no_mat": "Aucune émission significative déclarée.",
        "pdf_avail": "Disponible sur demande de l'acheteur",
        "pdf_attached": "fichiers joints",
        "pdf_no_files": "Aucun fichier numérique joint",
        
        "pdf_attest_title": "ATTESTATION SUR L'HONNEUR :",
        "pdf_attest_text": "Je soussigné(e), <b>{signer}</b>, certifie que les données d'activité et le CA fournis sont exacts et sincères.",
        "pdf_sig": "Signature Autorisée",
        
        "pdf_disc_title": "AVERTISSEMENT :",
        "pdf_disc_main": "Ce rapport utilise des données fournies par le fournisseur et les facteurs ADEME Base Carbone. Il n'a pas été vérifié indépendamment.",
        "pdf_exclusion_intro": "<b>Exclusions du Périmètre :</b> Les sources suivantes ont été évaluées mais exclues (activité nulle déclarée) :",
        "pdf_exclusion_none": "<b>Exclusions :</b> Aucune (Toutes les catégories standard ont été déclarées).",
        "pdf_disc_verify": "Les acheteurs doivent effectuer leurs vérifications pour le reporting CSRD. Pour vérification tierce : <b>verify@vsme.io</b>",
        
        "footer_l1": "Généré par VSME Supplier ESG OS",
        "footer_l2": "Aligné avec les méthodologies de quantification GHG Protocol & ISO 14064-1.",
        "footer_l3": "Supporte les exigences de reporting quantitatif CSRD ESRS E1.",
        "footer_l4": "Facteurs d'Émission : ADEME Base Carbone v23.0 (France)",
        
        # Evidence Labels
        "ev_gas": "Factures de Gaz Naturel",
        "ev_oil": "Factures d'achat Fioul",
        "ev_prop": "Factures d'achat Propane",
        "ev_diesel": "Relevés/Factures Carburant (Diesel)",
        "ev_petrol": "Relevés/Factures Carburant (Essence)",
        "ev_hvac": "Carnet d'entretien CVC (Fluides Frigorigènes)",
        "ev_elec": "Factures d'Électricité",
        "ev_heat": "Factures Chauffage Urbain",
        "ev_travel": "Notes de Frais / Relevés Kilométriques"
    }
}

# --- 2. DATA CLASSES & LOGIC ---
@dataclass
class ActivityInput:
    key: str # Internal ID for logic
    quantity: float
    unit: str
    category: str

@dataclass
class Factor:
    key: str
    value: float
    unit: str
    source: str
    id: str

# Helper to get activity label based on lang
def get_activity_label(key, lang):
    # Map internal keys to translation keys
    map_keys = {
        "natural_gas": "gas_label", "heating_oil": "oil_label", "propane": "propane_label",
        "diesel": "diesel_label", "petrol": "petrol_label",
        "ref_R410A": "r410a_label", "ref_R32": "r32_label", "ref_R134a": "r134a_label",
        "electricity_fr": "elec_label", "district_heat": "heat_label",
        "grey_fleet_avg": "grey_label"
    }
    t_key = map_keys.get(key, key)
    # Remove unit from label for clean display in table if needed, or keep it
    raw_label = TRANSLATIONS[lang].get(t_key, key)
    return raw_label.split("(")[0].strip() # Return just the name part "Natural Gas"

def calculate_emissions(inputs, factors, lang):
    rows = []
    for key, act in inputs.items():
        if act.quantity <= 0: continue
        
        factor = factors.get(key)
        if not factor: continue
        
        emissions = act.quantity * factor.value
        
        # Get translated Label
        display_label = get_activity_label(key, lang)
        
        rows.append({
            "Scope": act.category.split(" - ")[0], 
            "Category": act.category,
            "Activity": display_label,
            "Quantity": act.quantity,
            "Unit": act.unit,
            "FactorRef": f"{factor.value} ({factor.unit})",
            "Emissions_kgCO2e": emissions,
            "Source": f"{factor.source} [{factor.id}]"
        })
    return pd.DataFrame(rows)

def summarize(df):
    if df.empty: return {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0, "total": 0.0}
    s1 = df[df["Scope"] == "Scope 1"]["Emissions_kgCO2e"].sum()
    s2 = df[df["Scope"] == "Scope 2"]["Emissions_kgCO2e"].sum()
    s3 = df[df["Scope"] == "Scope 3"]["Emissions_kgCO2e"].sum()
    return {"scope1": s1, "scope2": s2, "scope3": s3, "total": s1 + s2 + s3}

# --- 3. PDF GENERATOR (Bilingual) ---
def build_pdf(company_name, country, year, revenue, currency, df, totals, evidence_files, signer_name, input_keys, lang):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Carbon Footprint - {company_name}", topMargin=30, bottomMargin=60)
    styles = getSampleStyleSheet()
    story = []
    
    T = TRANSLATIONS[lang]

    # 1. HEADER
    date_str = datetime.now().strftime('%d %b %Y')
    story.append(Paragraph(f"<b>{T['pdf_title']}</b>", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(T['pdf_method'], styles['Normal']))
    story.append(Paragraph(f"{T['pdf_date']} {date_str}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # 2. COMPANY DETAILS
    info_text = f"""
    <b>{T['pdf_company']}</b> {company_name}<br/>
    <b>{T['pdf_country']}</b> {country}<br/>
    <b>{T['pdf_period']}</b> {year}<br/>
    <b>{T['pdf_revenue']}</b> {revenue:,.2f} {currency}<br/>
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 15))

    # 3. BOUNDARY STATEMENT
    story.append(Paragraph(T['pdf_boundary_text'], styles['Normal']))
    story.append(Spacer(1, 20))

    # 4. SUMMARY DASHBOARD
    carbon_intensity = (totals['total'] / revenue) if revenue > 0 else 0
    
    story.append(Paragraph(f"<b>{T['pdf_summary_title']}</b>", styles['Heading3']))
    story.append(Spacer(1, 5))

    summary_data = [
        [T['pdf_col_metric'], T['pdf_col_value']], 
        [T['pdf_s1'], f"{totals['scope1']:,.2f} kgCO2e"],
        [T['pdf_s2'], f"{totals['scope2']:,.2f} kgCO2e"],
        [T['pdf_s3'], f"{totals['scope3']:,.2f} kgCO2e"],
        [T['pdf_total'], f"{totals['total']:,.2f} kgCO2e"], 
        [T['pdf_intensity'], f"{carbon_intensity:.2f} kgCO2e / {currency}"] 
    ]
    
    t_summary = Table(summary_data, colWidths=[250, 150])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (0, 3), 'Helvetica'),
        ('BACKGROUND', (0, 4), (-1, 4), colors.navy),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.white),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TOPPADDING', (0, 4), (-1, 4), 8),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 8),
        ('BACKGROUND', (0, 5), (-1, 5), colors.aliceblue),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Oblique'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    # 5. DETAILED TABLE
    if not df.empty:
        story.append(Paragraph(f"<b>{T['pdf_detail_title']}</b>", styles['Heading4']))
        data = [[T['pdf_tab_scope'], T['pdf_tab_act'], T['pdf_tab_qty'], T['pdf_tab_emi']]]
        for _, row in df.iterrows():
            qty_clean = f"{row['Quantity']:,.2f} {row['Unit']}"
            data.append([
                row['Scope'],
                row['Activity'],
                qty_clean,
                f"{row['Emissions_kgCO2e']:,.2f}"
            ])
        
        t = Table(data, colWidths=[60, 140, 80, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

    # --- 6. CLOSING BLOCK (Evidence + Attestation + Disclaimer) ---
    closing_elements = []

    # A. EVIDENCE SECTION
    closing_elements.append(Paragraph(f"<b>{T['pdf_evidence_title']}</b>", styles['Heading4']))
    
    # We use 'input_keys' (the raw IDs) to decide what evidence to show, ensuring translation safety
    required_evidence = []
    
    # Mapping raw keys to translated evidence labels
    if any(k in input_keys for k in ["natural_gas"]): required_evidence.append(T['ev_gas'])
    if any(k in input_keys for k in ["heating_oil"]): required_evidence.append(T['ev_oil'])
    if any(k in input_keys for k in ["propane"]): required_evidence.append(T['ev_prop'])
    if any(k in input_keys for k in ["diesel"]): required_evidence.append(T['ev_diesel'])
    if any(k in input_keys for k in ["petrol"]): required_evidence.append(T['ev_petrol'])
    if any(k in input_keys for k in ["ref_R410A", "ref_R32", "ref_R134a"]): required_evidence.append(T['ev_hvac'])
    if any(k in input_keys for k in ["electricity_fr"]): required_evidence.append(T['ev_elec'])
    if any(k in input_keys for k in ["district_heat"]): required_evidence.append(T['ev_heat'])
    if any(k in input_keys for k in ["grey_fleet_avg"]): required_evidence.append(T['ev_travel'])

    if not required_evidence:
        evidence_html = f"{T['pdf_no_mat']}<br/>"
    else:
        evidence_html = ""
        for item in list(set(required_evidence)): # Deduplicate
            evidence_html += f"&bull; {item}<br/>"
    
    file_msg = f"({len(evidence_files)} {T['pdf_attached']})" if evidence_files else f"({T['pdf_no_files']})"
    
    evidence_text = f"""
    {T['pdf_assurance_level']}<br/><br/>
    {T['pdf_doc_retained']}<br/>
    {evidence_html}
    <i>{T['pdf_avail']} {file_msg}</i>
    """
    closing_elements.append(Paragraph(evidence_text, styles['Normal']))
    closing_elements.append(Spacer(1, 30))

    # B. ATTESTATION
    sig_text = f"""
    <b>{T['pdf_attest_title']}</b><br/>
    {T['pdf_attest_text'].format(signer=signer_name)}
    <br/><br/>
    __________________________<br/>
    {T['pdf_sig']}
    """
    closing_elements.append(Paragraph(sig_text, styles['Normal']))
    closing_elements.append(Spacer(1, 20))
    
    # C. DISCLAIMER (Negative Assurance)
    # Define excluded items based on missing keys
    all_possible_keys = [
        "natural_gas", "heating_oil", "propane", 
        "diesel", "petrol", 
        "ref_R410A", "electricity_fr", "district_heat", "grey_fleet_avg"
    ]
    
    excluded_keys = [k for k in all_possible_keys if k not in input_keys]
    
    disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7, textColor=colors.grey, leading=9)
    
    if excluded_keys:
        # We need to map these keys to human readable labels (translated)
        # Reuse get_activity_label but generic
        labels = [get_activity_label(k, lang) for k in excluded_keys]
        # Consolidate refrigerants for cleaner list
        labels = [l for l in labels if "R410A" not in l] 
        if "ref_R410A" in excluded_keys and "ref_R32" in excluded_keys:
            labels.append("Refrigerants/Fluides")
            
        exclusion_str = ", ".join(labels)
        exclusion_msg = f"{T['pdf_exclusion_intro']} {exclusion_str}."
    else:
        exclusion_msg = T['pdf_exclusion_none']

    disclaimer_text = f"""
    <b>{T['pdf_disc_title']}</b> {T['pdf_disc_main']} {exclusion_msg}
    {T['pdf_disc_verify']}
    """
    closing_elements.append(Paragraph(disclaimer_text, disclaimer_style))

    story.append(KeepTogether(closing_elements))

    # --- 7. FOOTER ---
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0]/2, 42, T['footer_l1'])
        canvas.drawCentredString(A4[0]/2, 32, T['footer_l2'])
        canvas.drawCentredString(A4[0]/2, 22, T['footer_l3'])
        canvas.drawCentredString(A4[0]/2, 12, T['footer_l4'])
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buffer.getvalue()

# --- 4. APP UI ---
st.set_page_config(page_title="VSME Enterprise OS", page_icon="🏢")

# EMISSION FACTORS (Keys match the Translation Dictionary)
FACTORS = {
    "natural_gas": Factor("natural_gas", 0.244, "kgCO2e/kWh", "ADEME", "GAS-NAT"),
    "heating_oil": Factor("heating_oil", 3.2, "kgCO2e/L", "ADEME", "OIL-HEAT"),
    "propane": Factor("propane", 3.1, "kgCO2e/kg", "ADEME", "LPG-PROP"),
    "diesel": Factor("diesel", 3.16, "kgCO2e/L", "ADEME", "FUEL-DSL"),
    "petrol": Factor("petrol", 2.8, "kgCO2e/L", "ADEME", "FUEL-PET"),
    "ref_R410A": Factor("ref_R410A", 2088, "kgCO2e/kg", "ADEME", "REF-R410A"),
    "ref_R32": Factor("ref_R32", 675, "kgCO2e/kg", "ADEME", "REF-R32"),
    "ref_R134a": Factor("ref_R134a", 1430, "kgCO2e/kg", "ADEME", "REF-R134a"),
    "electricity_fr": Factor("electricity_fr", 0.052, "kgCO2e/kWh", "ADEME", "ELEC-FR"),
    "district_heat": Factor("district_heat", 0.170, "kgCO2e/kWh", "ADEME", "HEAT-NET"),
    "grey_fleet_avg": Factor("grey_fleet_avg", 0.218, "kgCO2e/km", "ADEME", "TRAVEL-CAR-AVG"),
}

# Session State for Language
if "lang" not in st.session_state: st.session_state.lang = "fr"
if "step" not in st.session_state: st.session_state.step = 1

# --- SIDEBAR LANGUAGE TOGGLE ---
with st.sidebar:
    lang_choice = st.radio("Language / Langue", ["Français", "English"])
    st.session_state.lang = "fr" if lang_choice == "Français" else "en"

# Shorcut for Translation Dict
T = TRANSLATIONS[st.session_state.lang]

st.title(T["title"])
st.caption(T["caption"])
st.progress(st.session_state.step / 3)

# STEP 1
if st.session_state.step == 1:
    st.header(T["step1_header"])
    comp_input = st.text_input(T["company_label"], value=st.session_state.get("company", ""))
    st.session_state.company = comp_input.strip().upper() if comp_input else ""
    st.session_state.country = st.text_input(T["country_label"], value=T["country_default"])
    st.session_state.year = st.text_input(T["year_label"], value="2025")
    
    c1, c2 = st.columns(2)
    with c1: 
        st.session_state.revenue = st.number_input(T["revenue_label"], min_value=0.0, step=1000.0, format="%.2f")
    with c2: 
        st.session_state.currency = st.selectbox(T["currency_label"], ["EUR", "USD", "GBP"])
        
    if st.button(T["btn_start"]):
        if st.session_state.company and st.session_state.revenue > 0:
            st.session_state.step = 2
            st.rerun()
        else:
            st.error(T["err_company"])

# STEP 2
elif st.session_state.step == 2:
    st.header(T["step2_header"])
    
    st.subheader(T["s1_header"])
    st.markdown(T["s1_stat"])
    c1, c2, c3 = st.columns(3)
    with c1: gas = st.number_input(T["gas_label"], min_value=0.0, format="%.2f")
    with c2: fioul = st.number_input(T["oil_label"], min_value=0.0, format="%.2f")
    with c3: propane = st.number_input(T["propane_label"], min_value=0.0, format="%.2f")

    st.markdown(T["s1_mobile"])
    c4, c5 = st.columns(2)
    with c4: diesel = st.number_input(T["diesel_label"], min_value=0.0, format="%.2f")
    with c5: petrol = st.number_input(T["petrol_label"], min_value=0.0, format="%.2f")
        
    st.markdown(T["s1_fugitive"])
    c6, c7, c8 = st.columns(3)
    with c6: r410a = st.number_input(T["r410a_label"], min_value=0.0, format="%.2f")
    with c7: r32 = st.number_input(T["r32_label"], min_value=0.0, format="%.2f")
    with c8: r134a = st.number_input(T["r134a_label"], min_value=0.0, format="%.2f")

    st.divider()
    st.subheader(T["s2_header"])
    c9, c10 = st.columns(2)
    with c9: elec = st.number_input(T["elec_label"], min_value=0.0, format="%.2f")
    with c10: heat = st.number_input(T["heat_label"], min_value=0.0, format="%.2f")

    st.divider()
    st.subheader(T["s3_header"])
    st.caption(T["s3_desc"])
    grey_km = st.number_input(T["grey_label"], min_value=0.0, format="%.2f")

    st.divider()
    files = st.file_uploader(T["upload_label"], accept_multiple_files=True)
    signer = st.text_input(T["signer_label"])

    if st.button(T["btn_gen"]):
        if not signer or len(signer) < 3:
            st.error(T["err_signer"])
        else:
            # We map inputs to their INTERNAL keys
            inputs = {
                "natural_gas": ActivityInput("natural_gas", gas, "kWh", "Scope 1 - Stationary"),
                "heating_oil": ActivityInput("heating_oil", fioul, "Liters", "Scope 1 - Stationary"),
                "propane": ActivityInput("propane", propane, "kg", "Scope 1 - Stationary"),
                "diesel": ActivityInput("diesel", diesel, "Liters", "Scope 1 - Mobile"),
                "petrol": ActivityInput("petrol", petrol, "Liters", "Scope 1 - Mobile"),
                "ref_R410A": ActivityInput("ref_R410A", r410a, "kg", "Scope 1 - Fugitive"),
                "ref_R32": ActivityInput("ref_R32", r32, "kg", "Scope 1 - Fugitive"),
                "ref_R134a": ActivityInput("ref_R134a", r134a, "kg", "Scope 1 - Fugitive"),
                "electricity_fr": ActivityInput("electricity_fr", elec, "kWh", "Scope 2 - Energy"),
                "district_heat": ActivityInput("district_heat", heat, "kWh", "Scope 2 - Energy"),
                "grey_fleet_avg": ActivityInput("grey_fleet_avg", grey_km, "km", "Scope 3 - Business Travel"),
            }
            
            # Identify active keys for evidence logic
            active_keys = [k for k, v in inputs.items() if v.quantity > 0]
            
            df = calculate_emissions(inputs, FACTORS, st.session_state.lang)
            st.session_state.results_df = df
            st.session_state.totals = summarize(df)
            st.session_state.evidence = [f.name for f in files] if files else []
            st.session_state.signer = signer
            st.session_state.input_keys = active_keys
            st.session_state.step = 3
            st.rerun()

# STEP 3
elif st.session_state.step == 3:
    st.header(T["step3_header"])
    t = st.session_state.totals
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Scope 1", f"{t['scope1']:,.2f}", "kgCO2e")
    c2.metric("Scope 2", f"{t['scope2']:,.2f}", "kgCO2e")
    c3.metric("Scope 3", f"{t['scope3']:,.2f}", "kgCO2e")
    st.metric(T["total_footprint"], f"{t['total']:,.2f} kgCO2e")
    
    pdf_data = build_pdf(
        st.session_state.company, st.session_state.country, st.session_state.year,
        st.session_state.revenue, st.session_state.currency,
        st.session_state.results_df, st.session_state.totals, st.session_state.evidence, st.session_state.signer,
        st.session_state.input_keys, st.session_state.lang
    )
    
    st.download_button(T["btn_download"], data=pdf_data, file_name="Carbon_Pack.pdf", mime="application/pdf")
    if st.button(T["btn_new"]):
        st.session_state.step = 1
        st.rerun()
