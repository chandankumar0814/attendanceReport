import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 1. Configure the API Key
GEMINI_API_KEY = "AIzaSyCqS9flyeUi8Lcvn_nEbH0jDCNe3oIxB0w"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="AI Attendance Scanner", layout="wide")

st.title("📑 AI Attendance Scanner for Pallavi")
st.info("This app uses Gemini AI to read handwritten registers and calculate totals.")

uploaded_file = st.file_uploader("Upload Register Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Display the uploaded image
    img = Image.open(uploaded_file)
    st.image(img, caption="Register Preview", use_container_width=True)
    
    if st.button("🚀 Analyze Register"):
        with st.spinner("AI is processing the handwriting..."):
            try:
                # Initialize Gemini 1.5 Flash (Fast & Accurate for OCR)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Instruction for the AI
                prompt = """
                Analyze this attendance register image:
                1. Identify the Student Names in the first column.
                2. For each student, count the number of vertical tally marks '||' or '1' as 'Present'.
                3. Count 'Ab' or 'A' entries as 'Absent'.
                4. Calculate the 'Total Days' (Present + Absent).
                5. Format the output ONLY as a clean CSV table with these headers: 
                   Student Name, Present, Absent, Total Days
                """
                
                # Generate content from image
                response = model.generate_content([prompt, img])
                
                # Clean up the AI response to get the raw CSV data
                raw_text = response.text
                csv_start = raw_text.find("Student Name")
                if csv_start != -1:
                    clean_csv = raw_text[csv_start:].strip().replace('```', '')
                    
                    # Convert to DataFrame
                    df = pd.read_csv(io.StringIO(clean_csv))
                    
                    # Display Results
                    st.success("Analysis Complete!")
                    
                    # Summary Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Students Found", len(df))
                    c2.metric("Avg Attendance", f"{df['Present'].mean():.1f}")
                    c3.metric("Class Avg %", f"{(df['Present'].sum() / df['Total Days'].sum() * 100):.1f}%")
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Download Button
                    st.download_button(
                        label="📩 Download Excel (CSV)",
                        data=clean_csv,
                        file_name="attendance_report.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("The AI couldn't find a table structure. Try a clearer photo.")
                    st.write("AI Raw Response:", raw_text)
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

else:
    st.write("Please upload a clear photo of the register page to begin.")
