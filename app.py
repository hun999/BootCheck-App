import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="BootCheck", layout="wide")

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    h1, h2, h3 { color: #111111; font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -1px; }
    .stButton>button { background-color: #000000; color: #ffffff; border-radius: 2px; padding: 15px; width: 100%; font-weight: 500; text-transform: uppercase; }
    .stButton>button:hover { background-color: #222222; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM SETUP ---
engine = None # Alaphelyzetben üres
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in available_models if 'flash' in m.lower()), available_models[0])
        engine = genai.GenerativeModel(selected_model)
    else:
        st.error("Missing API Key. Please add 'GEMINI_API_KEY' to Streamlit Secrets.")
except Exception as e:
    st.error(f"System initialization failed: {e}")

# --- PDF GENERATOR ---
def create_pdf(report_text, brand, model_name):
    pdf = FPDF()
    pdf.add_page()
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "BOOTCHECK VERIFICATION REPORT", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Issued on: {datetime.date.today()}", ln=True)
    pdf.line(10, 35, 200, 35)
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"PRODUCT: {brand.upper()} {model_name.upper()}", ln=True)
    status_text = "INSPECTION REQUIRED"
    pdf.set_text_color(180, 0, 0)
    if any(word in clean_text.upper() for word in ["LEGIT", "AUTHENTIC", "VERIFIED"]):
        status_text = "VERIFIED AUTHENTIC"
        pdf.set_text_color(0, 100, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"STATUS: {status_text}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, clean_text)
    return bytes(pdf.output())

# --- UI CONTENT ---
st.title("BootCheck")
st.markdown("##### High-Precision Product Verification")

with st.sidebar:
    st.markdown("### Specifications")
    brand = st.selectbox("Brand", ["Nike", "Adidas", "Puma", "Mizuno", "UA", "New Balance"])
    user_model = st.text_input("Model Name", "Phantom GX Elite")
    tier = st.selectbox("Tier", ["Elite", "Pro", "Academy", "Club"])
    weight = st.number_input("Measured Weight (g)", value=215)
    st.divider()
    st.caption("Engine: 1.5.2 Pro")

st.markdown("### Evidence Upload")
col1, col2 = st.columns(2)
with col1:
    side_img = st.file_uploader("Side Profile", type=['jpg','png','jpeg'])
    sole_img = st.file_uploader("Soleplate", type=['jpg','png','jpeg'])
    tag_img = st.file_uploader("Inner Tag", type=['jpg','png','jpeg'])
with col2:
    heel_img = st.file_uploader("Heel Symmetry", type=['jpg','png','jpeg'])
    stitch_img = st.file_uploader("Construction/Stitching", type=['jpg','png','jpeg'])

if 'report' not in st.session_state:
    st.session_state.report = None

if st.button("RUN VERIFICATION"):
    if engine is None:
        st.error("The verification engine is not ready. Check your API Key in Settings > Secrets.")
    elif side_img and sole_img and tag_img:
        with st.spinner('Analyzing patterns and production markers...'):
            uploaded_list = [side_img, sole_img, tag_img]
            if heel_img: uploaded_list.append(heel_img)
            if stitch_img: uploaded_list.append(stitch_img)
            pil_images = [Image.open(i) for i in uploaded_list]
            prompt = f"Professional verification of {brand} {user_model} ({tier}). Weight: {weight}g. Verdict (LEGIT/FAKE), Score (0-100), detailed technical findings. English only."
            try:
                response = engine.generate_content([prompt] + pil_images)
                st.session_state.report = response.text
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    else:
        st.error("Upload at least 3 images.")

if st.session_state.report:
    st.divider()
    st.subheader("Verification Report")
    st.markdown(st.session_state.report)
    try:
        pdf_data = create_pdf(st.session_state.report, brand, user_model)
        st.download_button("Download PDF Report", data=pdf_data, file_name=f"BootCheck_{user_model}.pdf", mime="application/pdf")
    except Exception as e:
        st.warning(f"PDF error: {e}")
