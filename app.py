import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 1. Setup API (In Streamlit Cloud, use st.secrets for safety)
API_KEY = st.sidebar.text_input("Enter Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)

st.title("📊 AI Attendance Scanner for Pallavi")
st.write("Using Gemini AI to extract attendance marks directly from your photo.")

uploaded_file = st.file_uploader("Upload Register Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file and API_KEY:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Register", use_container_width=True)
    
    if st.button("Analyze with AI"):
        with st.spinner("AI is reading the handwriting..."):
            # Initialize the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # The Prompt: Telling the AI exactly how to format the data
            prompt = """
            Look at this attendance register. 
            1. Identify each student name.
            2. Count the '||' symbols as 'Present'.
            3. Count 'Ab' as 'Absent'.
            4. Return the data ONLY as a valid CSV table with headers: 
               Student Name, Present, Absent
            """
            
            # Send image and prompt to API
            response = model.generate_content([prompt, img])
            
            # 2. Display Result
            try:
                # Clean the response to ensure it's just CSV data
                csv_data = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(csv_data))
                
                st.success("Analysis Complete!")
                st.table(df)
                
                # Download link
                st.download_button("📩 Download CSV", data=csv_data, file_name="attendance.csv")
            except Exception as e:
                st.error("The AI had trouble formatting the table. Here is the raw text:")
                st.write(response.text)
elif not API_KEY:
    st.warning("Please enter your Gemini API Key in the sidebar to start.")
