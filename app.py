import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from streamlit_cropper import st_cropper

st.set_page_config(page_title="Attendance Scan", layout="centered")

st.title("📊 Register Scanner")
st.write("Crop the image to focus on the **Names and Dots**.")

uploaded_file = st.file_uploader("Upload Register Photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # 1. The Cropper Tool
    # This allows you to select the exact table area on your phone
    cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None)
    
    st.write("Preview of Scanned Area:")
    st.image(cropped_img, use_container_width=True)

    # 2. Settings for the month
    total_working_days = st.number_input("Total Working Days in Month", min_value=1, value=25)

    if st.button("Calculate Stats"):
        with st.spinner("Analyzing grid..."):
            # Placeholder for OCR/Grid detection logic
            # In a live setup, this processes the 'cropped_img'
            data = {
                "Student": ["KUNDANGIRI KUMAR", "KESHAV KUMAR", "PUSHKAR SINGH", "ABHISHEK", "ADITYA"],
                "Total Present": [24, 23, 22, 25, 20] 
            }
            df = pd.DataFrame(data)
            
            # MATH SECTION
            # Average Daily Attendance = Total Presence / Total Working Days
            total_attendance_sum = df['Total Present'].sum()
            avg_daily_attendance = total_attendance_sum / total_working_days
            overall_pct = (total_attendance_sum / (len(df) * total_working_days)) * 100

            # 3. Display Results
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Working Days", total_working_days)
            col2.metric("Avg Daily Attnd", f"{avg_daily_attendance:.2f}")
            col3.metric("Overall %", f"{overall_pct:.1f}%")
            
            st.table(df)