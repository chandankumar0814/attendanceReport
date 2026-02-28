import os
import shutil

# --- CRITICAL: Redirect all Paddle activities to /tmp (writable) ---
# This MUST stay at the very top of the script
os.environ['PADDLE_HOME'] = '/tmp/.paddle'
os.environ['XDG_CACHE_HOME'] = '/tmp/.cache'
os.environ['FLAGS_use_mkldnn'] = '0'

import streamlit as st
import pandas as pd
import numpy as np
import cv2
import logging
from PIL import Image
from streamlit_cropper import st_cropper
from paddleocr import PaddleOCR

# Silence technical background logs
logging.getLogger("ppocr").setLevel(logging.ERROR)

@st.cache_resource
def load_ocr():
    """Initializes PaddleOCR with server-safe settings."""
    return PaddleOCR(
        use_angle_cls=True, 
        lang='en', 
        enable_mkldnn=False, 
        vis_font_path=None, # DIRECT FIX for PingFang-SC-Regular.ttf error
        show_log=False
    )

# Pre-initialize engine
try:
    ocr_engine = load_ocr()
except Exception as e:
    st.error(f"Engine Load Error: {e}")

st.set_page_config(page_title="Attendance Pro", layout="wide")
st.title("📊 Attendance Scanner for Pallavi")
st.markdown("Scan handwritten registers, detect `||` and `Ab`, and calculate monthly stats.")

uploaded_file = st.file_uploader("Upload Register Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    st.subheader("Step 1: Crop the Name & Attendance Area")
    # This allows the user to select the specific grid on their phone/PC
    cropped_img = st_cropper(img, realtime_update=True, box_color='#00FF00', aspect_ratio=None)
    
    if st.button("Analyze Register"):
        with st.spinner("PaddleOCR is scanning the table..."):
            # 1. Convert Image to BGR (required for PaddleOCR)
            img_array = np.array(cropped_img)
            img_for_ocr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # 2. Perform OCR
            result = ocr_engine.ocr(img_for_ocr)
            
            # 3. Group Text into Rows based on vertical (Y) position
            rows = {}
            if result and result[0]:
                for line in result[0]:
                    coords = line[0]
                    text = line[1][0].strip()
                    # Sensitivity: Group text within 30 pixels vertically
                    y_key = int(coords[0][1] / 30) * 30 
                    
                    if y_key not in rows: rows[y_key] = []
                    rows[y_key].append(text)

            # 4. Generate Attendance Data
            final_data = []
            for y in sorted(rows.keys()):
                full_text = " ".join(rows[y])
                
                # Logic for specific symbols: || (Present), Ab (Absent)
                # We also check for '11' or 'll' as OCR often reads handwritten '||' this way
                p_count = full_text.count("||") + full_text.count("11") + full_text.count("ll")
                a_count = full_text.lower().count("ab")
                
                if p_count + a_count > 0:
                    # Clean the name from the text (everything before the first mark)
                    name_part = full_text.split("||")[0].split("11")[0].split("Ab")[0].strip()
                    final_data.append({
                        "Student Name": name_part if len(name_part) > 2 else f"Student_{y}",
                        "Present": p_count,
                        "Absent": a_count
                    })

            if not final_data:
                st.warning("No marks detected. Please crop closer to the names and marks.")
            else:
                df = pd.DataFrame(final_data)
                df['Working Days'] = df['Present'] + df['Absent']
                df['Attendance %'] = (df['Present'] / df['Working Days']) * 100

                # 5. Display Stats & Table
                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("Max Working Days", int(df['Working Days'].max()))
                c2.metric("Avg Daily Presence", f"{df['Present'].mean():.2f}")
                c3.metric("Class Average %", f"{df['Attendance %'].mean():.1f}%")

                st.table(df[["Student Name", "Present", "Absent", "Attendance %"]])
                
                # Export to CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📩 Download CSV Report", data=csv, file_name="attendance_report.csv")
