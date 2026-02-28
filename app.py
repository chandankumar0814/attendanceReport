import os
# --- FIX 1: Redirect Paddle and Cache to writable /tmp folder ---
os.environ['PADDLE_HOME'] = '/tmp/.paddle'
os.environ['XDG_CACHE_HOME'] = '/tmp/.cache'
# --- FIX 2: Disable broken CPU acceleration on Streamlit servers ---
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'

import streamlit as st
import pandas as pd
import numpy as np
import cv2
import logging
from PIL import Image
from streamlit_cropper import st_cropper
from paddleocr import PaddleOCR

# Silence technical logs
logging.getLogger("ppocr").setLevel(logging.ERROR)

@st.cache_resource
def load_ocr():
    # --- FIX 3: Disable font loading and MKLDNN ---
    return PaddleOCR(
        use_angle_cls=True, 
        lang='en', 
        enable_mkldnn=False, 
        vis_font_path=None  # Tells Paddle not to try writing the font file
    )

ocr_engine = load_ocr()

st.set_page_config(page_title="Attendance Pro", layout="wide")
st.title("📊 Attendance Scanner for Pallavi")

uploaded_file = st.file_uploader("Upload Register Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.subheader("Step 1: Crop the Register Data")
    # Mobile-friendly cropping tool
    cropped_img = st_cropper(img, realtime_update=True, box_color='#00FF00', aspect_ratio=None)
    
    if st.button("Run Scan"):
        with st.spinner("PaddleOCR is scanning the table..."):
            # Image Conversion (Streamlit RGB -> Paddle BGR)
            img_array = np.array(cropped_img)
            img_for_ocr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Perform OCR (using the fixed engine)
            result = ocr_engine.ocr(img_for_ocr)
            
            # Group Text by Rows
            rows = {}
            if result and result[0]:
                for line in result[0]:
                    coords, (text, score) = line
                    y_key = int(coords[0][1] / 30) * 30 
                    if y_key not in rows: rows[y_key] = []
                    rows[y_key].append(text)

            # Process Final Table
            final_data = []
            for y in sorted(rows.keys()):
                full_text = " ".join(rows[y])
                p_count = full_text.count("||") + full_text.count("11") + full_text.count("ll")
                a_count = full_text.lower().count("ab")
                
                if p_count + a_count > 0:
                    name = full_text.split("||")[0].split("Ab")[0].strip()
                    final_data.append({
                        "Student Name": name if len(name) > 2 else f"Student_{y}",
                        "Present": p_count,
                        "Absent": a_count
                    })

            if final_data:
                df = pd.DataFrame(final_data)
                df['Attendance %'] = (df['Present'] / (df['Present'] + df['Absent'])) * 100
                
                st.divider()
                st.table(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📩 Download CSV Report", data=csv, file_name="attendance.csv")
            else:
                st.error("No data found. Try cropping closer to the text.")
