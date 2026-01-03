import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime
from dataclasses import dataclass

# --- 1. THE BRAIN (Calculation Logic) ---
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
        
        factor = factors.get(key)
        if not factor: continue
        
        emissions = act.quantity * factor.value
        rows.append({
            "Scope": act.category.split(" - ")[0], 
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
    if df.empty: return {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0, "total": 0.0}
    s1 = df[df["Scope"] == "Scope 1"]["Emissions_kgCO2e"].sum()
    s2 = df[df["Scope"] == "Scope 2"]["Emissions_kgCO2e"].sum()
    s3 = df[df["Scope"] == "Scope 3"]["Emissions_kgCO2e"].sum()
    return {"scope1": s1, "scope2": s2, "scope3": s3, "total": s1 + s2 + s3}

# --- 2. THE PDF GENERATOR (With Branding Footer) ---
def build_pdf(company_name, country, year, revenue, currency, df, totals, evidence_files, signer_name):
    buffer = BytesIO()
    # TOP MARGIN set to 30, BOTTOM MARGIN set to 40 to make room for footer
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Carbon Footprint - {company_name}", topMargin=30, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # --- CONTENT GENERATION ---
    
    # 1. HEADER (Formal)
    date_str = datetime.now().strftime('%d %b %Y')
    story.append(Paragraph("<b>CORPORATE CARBON FOOTPRINT DECLARATION</b>", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Methodology Aligned with GHG Protocol & ISO 14064-1", styles['Normal']))
    story.append(Paragraph(f"Date: {date_str}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # 2. COMPANY DETAILS
    info_text = f"""
    <b>Company Name:</b> {company_name}<br/>
    <b>Site Country:</b> {country}<br/>
    <b>Reporting Period:</b> {year}<br/>
    <b>Annual Revenue:</b> {revenue:,.2f} {currency}<br/>
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 15))

    # 3. BOUNDARY STATEMENT
    boundary_text = """
    <b>BOUNDARY STATEMENT:</b><br/>
    This report covers <b>Scope 1</b> (Direct), <b>Scope 2</b> (Energy Indirect), and selected <b>Scope 3</b> 
    (Grey Fleet / Business Travel). Excludes upstream/downstream Scope 3 categories unless noted.
    Calculations use <b>ADEME Base Carbone</b> emission factors.
    """
    story.append(Paragraph(boundary_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # 4. SUMMARY DASHBOARD
    carbon_intensity = (totals['total'] / revenue) if revenue > 0 else 0
    
    story.append(Paragraph("<b>EMISSIONS SUMMARY</b>", styles['Heading3']))
    story.append(Spacer(1, 5))

    summary_data = [
        ["METRIC", "VALUE"], 
        ["Scope 1 (Direct Emissions)", f"{totals['scope1']:,.2f} kgCO2e"],
        ["Scope 2 (Indirect Energy)", f"{totals['scope2']:,.2f} kgCO2e"],
        ["Scope 3 (Grey Fleet)", f"{totals['scope3']:,.2f} kgCO2e"],
        ["TOTAL FOOTPRINT", f"{totals['total']:,.2f} kgCO2e"], 
        ["CARBON INTENSITY", f"{carbon_intensity:.2f} kgCO2e / {currency}"] 
    ]
    
    t_summary = Table(summary_data, colWidths=[250, 150])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (0, 3), 'Helvetica'),
        # Total Row
        ('BACKGROUND', (0, 4), (-1, 4), colors.navy),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.white),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TOPPADDING', (0, 4), (-1, 4), 8),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 8),
        # Intensity Row
        ('BACKGROUND', (0, 5), (-1, 5), colors.aliceblue),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Oblique'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    # 5. DETAILED TABLE
    if not df.empty:
        story.append(Paragraph("<b>Detailed Breakdown:</b>", styles['Heading4']))
        data = [["Scope", "Activity", "Qty", "Emissions (kg)"]]
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

    # 6. EVIDENCE & ASSURANCE
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Evidence & Assurance:</b>", styles['Heading4']))
    
    num_files = len(evidence_files)
    if num_files > 0:
        evidence_text = f"Self-declared by supplier. Evidence attached: {num_files} file(s)."
    else:
        evidence_text = "Self-Declaration (No supporting evidence attached)."
        
    story.append(Paragraph(evidence_text, styles['Normal']))
    
    story.append(Spacer(1, 30))
    sig_text = f"""
    <b>ATTESTATION:</b><br/>
    I, <b>{signer_name}</b>, certify that the activity data and revenue provided are accurate to the best of my knowledge.
    <br/><br/>
    __________________________<br/>
    Authorized Signature
    """
    story.append(Paragraph(sig_text, styles['Normal']))

    # --- FOOTER FUNCTION ---
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        # Centered Footer
        canvas.drawCentredString(A4[0]/2, 20, "Generated by VSME Supplier ESG OS • Methodology Aligned with GHG Protocol")
        canvas.restoreState()

    # BUILD PDF with Footer on all pages
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buffer.getvalue()

# --- 3. THE APP (UI) ---
st.set_page_config(page_title="VSME Enterprise OS", page_icon="🏢")

# EMISSION FACTORS (ADEME / BASE CARBONE)
FACTORS = {
    "natural_gas": Factor("Natural Gas", 0.244, "kgCO2e/kWh", "ADEME", "GAS-NAT"),
    "heating_oil": Factor("Heating Oil", 3.2, "kgCO2e/L", "ADEME", "OIL-HEAT"),
    "propane": Factor("Propane", 3.1, "kgCO2e/kg", "ADEME", "LPG-PROP"),
    "diesel": Factor("Fleet Diesel", 3.16, "kgCO2e/L", "ADEME", "FUEL-DSL"),
    "petrol": Factor("Fleet Petrol", 2.8, "kgCO2e/L", "ADEME", "FUEL-PET"),
    "ref_R410A": Factor("Refill R410A", 2088, "kgCO2e/kg", "ADEME", "REF-R410A"),
    "ref_R32": Factor("Refill R32", 675, "kgCO2e/kg", "ADEME", "REF-R32"),
    "ref_R134a": Factor("Refill R134a", 1430, "kgCO2e/kg", "ADEME", "REF-R134a"),
    "electricity_fr": Factor("Electricity (FR Mix)", 0.052, "kgCO2e/kWh", "ADEME", "ELEC-FR"),
    "district_heat": Factor("District Heating", 0.170, "kgCO2e/kWh", "ADEME", "HEAT-NET"),
    "grey_fleet_avg": Factor("Grey Fleet (Avg Car)", 0.218, "kgCO2e/km", "ADEME", "TRAVEL-CAR-AVG"),
}

if "step" not in st.session_state: st.session_state.step = 1

st.title("🏢 Supplier ESG Enterprise OS")
st.caption("Aligned with GHG Protocol (Scope 1, 2 & Grey Fleet)")
st.progress(st.session_state.step / 3)

# STEP 1: COMPANY PROFILE
if st.session_state.step == 1:
    st.header("Step 1: Company Profile")
    
    # Auto-Capitalize Company Name for professional look
    comp_input = st.text_input("Company Legal Name", value=st.session_state.get("company", ""))
    st.session_state.company = comp_input.strip().upper() if comp_input else ""
    
    st.session_state.country = st.text_input("Site Country", value="France")
    st.session_state.year = st.text_input("Reporting Period", value="2025")
    
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.revenue = st.number_input("Annual Revenue", min_value=0.0, step=1000.0, format="%.2f")
    with c2:
        st.session_state.currency = st.selectbox("Currency", ["EUR", "USD", "GBP"])
        
    if st.button("Start Assessment"):
        if st.session_state.company and st.session_state.revenue > 0:
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Company Name and Revenue are required.")

# STEP 2: DATA INPUT
elif st.session_state.step == 2:
    st.header("Step 2: Activity Data")
    
    st.subheader("🔥 Scope 1: Direct Emissions")
    st.markdown("**Stationary Combustion**")
    c1, c2, c3 = st.columns(3)
    with c1: gas = st.number_input("Natural Gas (kWh)", min_value=0.0, format="%.2f")
    with c2: fioul = st.number_input("Heating Oil (Liters)", min_value=0.0, format="%.2f")
    with c3: propane = st.number_input("Propane (kg)", min_value=0.0, format="%.2f")

    st.markdown("**Mobile Combustion (Company Fleet)**")
    c4, c5 = st.columns(2)
    with c4: diesel = st.number_input("Fleet Diesel (Liters)", min_value=0.0, format="%.2f")
    with c5: petrol = st.number_input("Fleet Petrol (Liters)", min_value=0.0, format="%.2f")
        
    st.markdown("**Fugitive Emissions (Refrigerants)**")
    c6, c7, c8 = st.columns(3)
    with c6: r410a = st.number_input("R410A Refill (kg)", min_value=0.0, format="%.2f")
    with c7: r32 = st.number_input("R32 Refill (kg)", min_value=0.0, format="%.2f")
    with c8: r134a = st.number_input("R134a Refill (kg)", min_value=0.0, format="%.2f")

    st.divider()
    st.subheader("⚡ Scope 2: Indirect Energy")
    c9, c10 = st.columns(2)
    with c9: elec = st.number_input("Electricity (kWh)", min_value=0.0, format="%.2f")
    with c10: heat = st.number_input("District Heating (kWh)", min_value=0.0, format="%.2f")

    st.divider()
    st.subheader("🚗 Scope 3: Grey Fleet")
    st.caption("Business travel in employee-owned vehicles.")
    grey_km = st.number_input("Total Distance (km)", min_value=0.0, format="%.2f")

    st.divider()
    files = st.file_uploader("Upload Evidence", accept_multiple_files=True)
    
    # Signature Field
    signer = st.text_input("Full Legal Name of Authorized Signer (e.g. Jean Dupont)")

    if st.button("Generate Report"):
        # Validation
        if not signer or len(signer) < 3:
            st.error("Please enter a valid full name for the attestation signature.")
        else:
            inputs = {
                "natural_gas": ActivityInput("Natural Gas", gas, "kWh", "Scope 1 - Stationary"),
                "heating_oil": ActivityInput("Heating Oil", fioul, "Liters", "Scope 1 - Stationary"),
                "propane": ActivityInput("Propane", propane, "kg", "Scope 1 - Stationary"),
                "diesel": ActivityInput("Fleet Diesel", diesel, "Liters", "Scope 1 - Mobile"),
                "petrol": ActivityInput("Fleet Petrol", petrol, "Liters", "Scope 1 - Mobile"),
                "ref_R410A": ActivityInput("AC Refill R410A", r410a, "kg", "Scope 1 - Fugitive"),
                "ref_R32": ActivityInput("AC Refill R32", r32, "kg", "Scope 1 - Fugitive"),
                "ref_R134a": ActivityInput("AC Refill R134a", r134a, "kg", "Scope 1 - Fugitive"),
                "electricity_fr": ActivityInput("Electricity", elec, "kWh", "Scope 2 - Energy"),
                "district_heat": ActivityInput("District Heating", heat, "kWh", "Scope 2 - Energy"),
                "grey_fleet_avg": ActivityInput("Grey Fleet Travel", grey_km, "km", "Scope 3 - Business Travel"),
            }
            
            df = calculate_emissions(inputs, FACTORS)
            st.session_state.results_df = df
            st.session_state.totals = summarize(df)
            st.session_state.evidence = [f.name for f in files] if files else []
            st.session_state.signer = signer
            st.session_state.step = 3
            st.rerun()

# STEP 3: DOWNLOAD
elif st.session_state.step == 3:
    st.header("Step 3: Validated")
    t = st.session_state.totals
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Scope 1", f"{t['scope1']:,.2f}", "kgCO2e")
    c2.metric("Scope 2", f"{t['scope2']:,.2f}", "kgCO2e")
    c3.metric("Scope 3", f"{t['scope3']:,.2f}", "kgCO2e")
    
    st.metric("Total Footprint", f"{t['total']:,.2f} kgCO2e")
    
    # Build PDF with Footer and Signer
    pdf_data = build_pdf(
        st.session_state.company, st.session_state.country, st.session_state.year,
        st.session_state.revenue, st.session_state.currency,
        st.session_state.results_df, st.session_state.totals, st.session_state.evidence, st.session_state.signer
    )
    
    st.download_button("Download Corporate Carbon Pack (PDF)", data=pdf_data, file_name="Carbon_Pack.pdf", mime="application/pdf")
    if st.button("New Assessment"):
        st.session_state.step = 1
        st.rerun()
