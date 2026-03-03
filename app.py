import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Step 4: SETUP & CONFIGURATION ---
# --- Step 4: SETUP & CONFIGURATION ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialization with explicit stable versioning
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview') # Or 'gemini-2.5-flash'

# --- Step 5: UPDATED PROMPT TEMPLATES (Optimized for Markdown) ---
templates = {
    "Balance Sheet": """Analyze this Balance Sheet data. Use Markdown for formatting:
    # [Company Name] Balance Sheet Analysis
    - **Total Assets/Liabilities/Equity:** [Summarize]
    - **Significant Changes:** [List changes]
    - **Actionable Insights:** [3 points]
    Data: {data}""",
    
    "Profit and Loss": """Analyze this P&L Statement. Use Markdown for formatting:
    # [Company Name] P&L Analysis
    - **Revenue & Profit:** [Explain in simple terms]
    - **Profitability:** [Describe margins]
    - **CEO Summary:** [Bottom line result]
    Data: {data}""",
    
    "Cash Flow": """Analyze this Cash Flow Statement. Use Markdown for formatting:
    # [Company Name] Cash Flow Analysis
    - **Sources & Uses:** [Explain cash movement]
    - **Spending Spikes:** [Highlight unusual items]
    - **Headline:** [Write a news-style headline]
    Data: {data}"""
}

# --- Step 6.1: Load File with Explicit Cleaning ---
def load_file_content(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            # Force engine='python' to handle weird separators better
            df = pd.read_csv(uploaded_file, sep=',', engine='python') 
        else:
            df = pd.read_excel(uploaded_file)
        
        # Strip extra spaces from column names and values
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# --- Step 7: Generate Summary with Error Catching ---
def generate_summary(df, doc_type):
    if df is not None:
        # Clean data to string - avoid sending 'None' values to AI
        data_as_string = df.fillna(0).to_string()
        prompt = templates[doc_type].format(data=data_as_string)
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
            return "⚠️ AI returned an empty response. Try re-uploading the file."
        except Exception as e:
            return f"❌ AI Decoder Error: {str(e)}"
    return "No data provided."

# --- Step 9: MAIN APP INTERFACE ---
st.set_page_config(page_title="Financial Decoder", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("Gemini Pro Financial Decoder 📈")

# Uploaders
bs_file = st.file_uploader("Upload Balance Sheet", type=["csv", "xlsx"], key="bs")
pl_file = st.file_uploader("Upload Profit and Loss", type=["csv", "xlsx"], key="pl")
cf_file = st.file_uploader("Upload Cash Flow", type=["csv", "xlsx"], key="cf")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    generate_btn = st.button("🚀 Generate Reports", use_container_width=True)

if generate_btn:
    files_to_process = [(bs_file, "Balance Sheet"), (pl_file, "Profit and Loss"), (cf_file, "Cash Flow")]
    
    for uploaded_file, label in files_to_process:
        if uploaded_file is not None:
            df = load_file_content(uploaded_file)
            
            if df is not None:
                st.divider()
                st.header(f"{label} Summary")
                
                # --- AI Insights ---
                with st.spinner(f"Analyzing {label}..."):
                    summary = generate_summary(df, label)
                    # Force display as Markdown
                    st.markdown(summary)
                
                # --- Visual Analysis ---
                st.subheader("📊 Visual Trend")
                df_numeric = df.apply(lambda x: pd.to_numeric(x.astype(str).str.replace(r'[$, ]', '', regex=True), errors='coerce'))
                chart_data = df_numeric.select_dtypes(include=['number'])
                if not chart_data.empty:
                    st.line_chart(chart_data)

                # --- Data Table ---
                st.subheader("📋 Raw Data Table")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.error(f"Could not read {label}. Please ensure it is a valid CSV/XLSX.")