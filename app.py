import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime
from dataclasses import dataclass

# --- 1. THE BRAIN (Expanded for Full Scope 1 & 2) ---
@dataclass
class ActivityInput:
    label: str
    quantity: float
    unit: str
    category: str

@dataclass
class Factor:
    label: str
    value: float
    unit: str
    source: str
    id: str

def calculate_emissions(inputs, factors):
    rows = []
    for key, act in inputs.items():
        if act.quantity <= 0: continue
        
        # specific handling for refrigerants (dynamic keys)
        if key.startswith("ref_"):
            factor = factors.get(key)
        else:
            factor = factors.get(key)
            
        if not factor: continue
        
        emissions = act.quantity * factor.value
        rows.append({
            "Scope": "Scope 1" if act.category != "Scope 2" else "Scope 2",
            "Category": act.category,
            "Activity": act.label,
            "Quantity": act.quantity,
            "Unit": act.unit,
            "FactorRef": f"{factor.value} ({factor.unit})",
            "Emissions_kgCO2e": emissions,
            "Source": f"{factor.source} [{factor.id}]"
        })
    return pd.DataFrame(rows)

def summarize(df):
    if df.empty: return {"scope1": 0.0, "scope2": 0.0, "total": 0.0}
    s1 = df[df["Scope"] == "Scope 1"]["Emissions_kgCO2e"].sum()
    s2 = df[df["Scope"] == "Scope 2"]["Emissions_kgCO2e"].sum()
    return {"scope1": s1, "scope2": s2, "total": s1 + s2}

# --- 2. THE ENTERPRISE PDF GENERATOR (FIXED DECIMALS) ---
def build_pdf(company_name, country, year, df, totals, evidence_files, signer_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"ESG Declaration - {company_name}")
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>COMPREHENSIVE ESG DECLARATION (SCOPE 1 & 2)</b>", styles['Title']))
    story.append(Paragraph(f"Generated via VSME OS | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Company Block
    info_text = f"""
    <b>Company Name:</b> {company_name}<br/>
    <b>Site Country:</b> {country}<br/>
    <b>Reporting Period:</b> {year}<br/>
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 12))

    # Boundary
    boundary_text = """
    <b>BOUNDARY STATEMENT:</b><br/>
    This report covers all material <b>Scope 1</b> (Stationary Combustion, Mobile Combustion, Fugitive Emissions) 
    and <b>Scope 2</b> (Purchased Electricity & Heating/Cooling). Excludes Scope 3.
    Calculations utilize <b>ADEME Base Carbone</b> emission factors.
    """
    story.append(Paragraph(boundary_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # Summary
    summary_text = f"""
    <b>EMISSIONS SUMMARY:</b><br/>
    &nbsp;&nbsp;Scope 1 (Direct): <b>{totals['scope1']:,.2f} kgCO2e</b><br/>
    &nbsp;&nbsp;Scope 2 (Indirect): <b>{totals['scope2']:,.2f} kgCO2e</b><br/>
    &nbsp;&nbsp;<b>GRAND TOTAL: {totals['total']:,.2f} kgCO2e</b>
    """
    story.append(Paragraph(summary_text, styles['Heading3']))
    story.append(Spacer(1, 12))

    # Detailed Table
    if not df.empty:
        story.append(Paragraph("<b>Detailed Breakdown:</b>", styles['Heading4']))
        data = [["Scope", "Category", "Activity", "Qty", "Emissions (kg)"]]
        for _, row in df.iterrows():
            # FIXED: Used :.5g to limit decimals cleanly (e.g. 0.90000 -> 0.9)
            qty_clean = f"{row['Quantity']:,.5g} {row['Unit']}"
            data.append([
                row['Scope'],
                row['Category'],
                row['Activity'],
                qty_clean,
                f"{row['Emissions_kgCO2e']:,.2f}"
            ])
        
        t = Table(data, colWidths=[45, 90, 110, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)

    # Evidence & Signature
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Evidence Trail:</b>", styles['Heading4']))
    if evidence_files:
        for f in evidence_files: story.append(Paragraph(f"[ATTACHED] {f}", styles['Normal']))
    else: story.append(Paragraph("No evidence attached.", styles['Normal']))

    story.append(Spacer(1, 30))
    sig_text = f"""
    <b>ATTESTATION:</b><br/>
    I, <b>{signer_name}</b>, certify that the activity data provided is accurate and complete 
    to the best of my knowledge. This declaration covers all known material Scope 1 & 2 sources.
    <br/><br/>
    __________________________<br/>
    Authorized Signature
    """
    story.append(Paragraph(sig_text, styles['Normal']))

    doc.build(story)
    return buffer.getvalue()

# --- 3. THE APP (Full "Big Firm" UI) ---
st.set_page_config(page_title="VSME Enterprise OS", page_icon="🏢")

# EXPANDED FACTORS DATABASE (France Defaults)
FACTORS = {
    # Scope 2
    "electricity_fr": Factor("Electricity (FR Mix)", 0.052, "kgCO2e/kWh", "ADEME", "ELEC-FR"),
    "district_heat": Factor("District Heating (Avg)", 0.170, "kgCO2e/kWh", "ADEME", "HEAT-NET-FR"),
    
    # Scope 1 - Stationary
    "natural_gas": Factor("Natural Gas", 0.244, "kgCO2e/kWh", "ADEME", "GAS-NAT"),
    "heating_oil": Factor("Heating Oil (Fioul)", 3.2, "kgCO2e/L", "ADEME", "OIL-HEAT"),
    "propane": Factor("Propane", 3.1, "kgCO2e/kg", "ADEME", "LPG-PROP"),
    
    # Scope 1 - Mobile
    "diesel": Factor("Diesel (B7)", 3.16, "kgCO2e/L", "ADEME", "FUEL-DSL"),
    "petrol": Factor("Petrol (E10)", 2.8, "kgCO2e/L", "ADEME", "FUEL-PET"),
    
    # Scope 1 - Fugitive (Refrigerants)
    "ref_R410A": Factor("Refrigerant R410A", 2088, "kgCO2e/kg", "IPCC/ADEME", "REF-R410A"),
    "ref_R32": Factor("Refrigerant R32", 675, "kgCO2e/kg", "IPCC/ADEME", "REF-R32"),
    "ref_R134a": Factor("Refrigerant R134a", 1430, "kgCO2e/kg", "IPCC/ADEME", "REF-R134a"),
}

if "step" not in st.session_state: st.session_state.step = 1

st.title("🏢 Supplier ESG Enterprise OS")
st.caption("Complete Scope 1 & 2 Reporting (Stationary, Mobile, Fugitive)")
st.progress(st.session_state.step / 3)

if st.session_state.step == 1:
    st.header("Step 1: Entity Profile")
    st.session_state.company = st.text_input("Company Legal Name", value=st.session_state.get("company", ""))
    st.session_state.country = st.text_input("Site Country", value="France")
    st.session_state.year = st.text_input("Reporting Period", value="2025")
    if st.button("Start Assessment"):
        if st.session_state.company:
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Comprehensive Data Entry")
    
    # Scope 2 Section
    st.subheader("⚡ Scope 2: Purchased Energy")
    c1, c2 = st.columns(2)
    with c1:
        elec = st.number_input("Electricity (kWh)", min_value=0.0, step=100.0)
    with c2:
        heat = st.number_input("District Heating (kWh)", min_value=0.0, step=100.0, help="Réseau de Chaleur (CPCU etc.)")

    # Scope 1 Stationary
    st.subheader("🔥 Scope 1: Buildings & Stationary")
    c3, c4, c5 = st.columns(3)
    with c3:
        gas = st.number_input("Natural Gas (kWh)", min_value=0.0, step=100.0)
    with c4:
        fioul = st.number_input("Heating Oil/Fioul (Liters)", min_value=0.0, step=10.0)
    with c5:
        propane = st.number_input("Propane/LPG (kg)", min_value=0.0, step=10.0)

    # Scope 1 Mobile
    st.subheader("🚗 Scope 1: Fleet & Mobile")
    c6, c7 = st.columns(2)
    with c6:
        diesel = st.number_input("Vehicle Diesel (Liters)", min_value=0.0, step=10.0)
    with c7:
        petrol = st.number_input("Vehicle Petrol (Liters)", min_value=0.0, step=10.0)

    # Scope 1 Fugitive
    st.subheader("❄️ Scope 1: Fugitive (AC/Refrigerants)")
    st.caption("Did you refill any AC units or fridges this year? Enter the kg of gas added.")
    c8, c9, c10 = st.columns(3)
    with c8:
        r410a = st.number_input("R410A Added (kg)", min_value=0.0, step=0.1)
    with c9:
        r32 = st.number_input("R32 Added (kg)", min_value=0.0, step=0.1)
    with c10:
        r134a = st.number_input("R134a Added (kg)", min_value=0.0, step=0.1)

    st.divider()
    files = st.file_uploader("Upload Evidence (Invoices/Maintenance Logs)", accept_multiple_files=True)
    signer = st.text_input("Authorized Signer Name")

    if st.button("Generate Enterprise Report"):
        if not signer:
            st.error("Signature required.")
        else:
            inputs = {
                "electricity_fr": ActivityInput("Electricity", elec, "kWh", "Scope 2"),
                "district_heat": ActivityInput("District Heating", heat, "kWh", "Scope 2"),
                "natural_gas": ActivityInput("Natural Gas", gas, "kWh", "Stationary"),
                "heating_oil": ActivityInput("Heating Oil", fioul, "Liters", "Stationary"),
                "propane": ActivityInput("Propane", propane, "kg", "Stationary"),
                "diesel": ActivityInput("Vehicle Diesel", diesel, "Liters", "Mobile"),
                "petrol": ActivityInput("Vehicle Petrol", petrol, "Liters", "Mobile"),
                "ref_R410A": ActivityInput("Refrigerant R410A", r410a, "kg", "Fugitive"),
                "ref_R32": ActivityInput("Refrigerant R32", r32, "kg", "Fugitive"),
                "ref_R134a": ActivityInput("Refrigerant R134a", r134a, "kg", "Fugitive"),
            }
            
            df = calculate_emissions(inputs, FACTORS)
            st.session_state.results_df = df
            st.session_state.totals = summarize(df)
            st.session_state.evidence = [f.name for f in files] if files else []
            st.session_state.signer = signer
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Enterprise Pack Ready")
    t = st.session_state.totals
    c1, c2, c3 = st.columns(3)
    c1.metric("Scope 1", f"{t['scope1']:.2f}", "kgCO2e")
    c2.metric("Scope 2", f"{t['scope2']:.2f}", "kgCO2e")
    c3.metric("Grand Total", f"{t['total']:.2f}", "kgCO2e")
    
    st.table(st.session_state.results_df)
    
    pdf_data = build_pdf(
        st.session_state.company, st.session_state.country, st.session_state.year, 
        st.session_state.results_df, st.session_state.totals, st.session_state.evidence, st.session_state.signer
    )
    
    st.download_button("Download Signed Enterprise PDF", data=pdf_data, file_name="Enterprise_ESG_Pack.pdf", mime="application/pdf")
    if st.button("Start New Assessment"):
        st.session_state.step = 1
        st.rerun()