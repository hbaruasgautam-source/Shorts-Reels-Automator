import streamlit as st
import os
import time
from processor import VideoStacker

# --- CONFIGURATION ---
TEMP_DIR = "temp"
OUTPUT_DIR = "output"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="Vertical Video Stacker", layout="wide", page_icon="🎬")

# --- UI HEADER ---
st.title("🎬 Shorts & Reels Automator")
st.markdown("Stack two landscape videos into a viral vertical format.")
st.markdown("---")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ Processing Settings")

# Resolution
res_option = st.sidebar.selectbox("Output Resolution", ["1080x1920 (High Quality)", "720x1280 (Fast Render)"])
target_w, target_h = (1080, 1920) if "1080" in res_option else (720, 1280)

# Resize Mode
resize_mode = st.sidebar.radio("Resize Logic", ["crop", "fit", "stretch"], index=0)

# Duration Logic
duration_logic = st.sidebar.selectbox("Duration Handling", ["shortest", "loop_shortest", "manual"])
manual_dur = 0
if duration_logic == "manual":
    manual_dur = st.sidebar.number_input("Target Duration (seconds)", min_value=1, value=15)

# Audio Settings
st.sidebar.markdown("---")
st.sidebar.subheader("🔊 Audio Mixer")
audio_source = st.sidebar.selectbox("Audio Source", ["mix", "top", "bottom", "mute"])
vol_slider = st.sidebar.slider("Volume Level", 0.0, 2.0, 1.0)

# --- MAIN AREA: FILE UPLOAD & OFFSETS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("⬆️ Top Video")
    top_file = st.file_uploader("Select Top Video", type=['mp4', 'mov', 'avi'], key="top")
    top_offset = st.number_input("Start Top Video at (sec):", min_value=0.0, step=0.5, key="offset_top")

with col2:
    st.subheader("⬇️ Bottom Video")
    bot_file = st.file_uploader("Select Bottom Video", type=['mp4', 'mov', 'avi'], key="bot")
    bot_offset = st.number_input("Start Bottom Video at (sec):", min_value=0.0, step=0.5, key="offset_bot")

# --- ACTION BUTTONS ---
st.markdown("---")
if top_file and bot_file:
    # Save Uploads to Temp
    t_path = os.path.join(TEMP_DIR, top_file.name)
    b_path = os.path.join(TEMP_DIR, bot_file.name)
    
    # Write files only if they don't exist (saves SSD wear/time on re-runs)
    if not os.path.exists(t_path):
        with open(t_path, "wb") as f: f.write(top_file.getbuffer())
    if not os.path.exists(b_path):
        with open(b_path, "wb") as f: f.write(bot_file.getbuffer())
    
    st.success("✅ Files ready.")

    # Output Filename
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        out_name = st.text_input("Output Filename", "Sample")
    
    with c2:
        st.write("###") # Spacing
        btn_preview = st.button("👁️ Preview (5s)", use_container_width=True)
    
    with c3:
        st.write("###") # Spacing
        btn_render = st.button("🚀 Full Render", type="primary", use_container_width=True)

    # --- PROCESSING FUNCTION ---
    def run_process(is_preview_mode):
        status_text = st.empty()
        status_text.text("Initializing Processor...")
        
        final_filename = f"{out_name}_PREVIEW.mp4" if is_preview_mode else f"{out_name}.mp4"
        out_path = os.path.join(OUTPUT_DIR, final_filename)

        stacker = VideoStacker(t_path, b_path, out_path)
        
        # Apply UI Settings to Class
        stacker.target_width = target_w
        stacker.target_height = target_h
        stacker.resize_mode = resize_mode.lower()
        stacker.duration_mode = duration_logic
        stacker.manual_duration = manual_dur
        stacker.audio_mode = audio_source
        stacker.volume = vol_slider
        
        # NEW: Apply Offsets & Preview Flag
        stacker.top_offset = top_offset
        stacker.bottom_offset = bot_offset
        stacker.is_preview = is_preview_mode

        loaded, msg = stacker.load_clips()
        if not loaded:
            st.error(msg)
            return
        
        with st.spinner("Processing... Please Wait"):
            try:
                start_time = time.time()
                final_path = stacker.render()
                end_time = time.time()
                
                st.success(f"Done! ({round(end_time - start_time, 2)}s)")
                st.video(final_path)
                
                with open(final_path, "rb") as file:
                    st.download_button(
                        label="Download Video",
                        data=file,
                        file_name=final_filename,
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"Error: {e}")

    # --- BUTTON LOGIC ---
    if btn_preview:
        run_process(is_preview_mode=True)
        
    if btn_render:
        run_process(is_preview_mode=False)

else:
    st.info("👋 Upload videos to unlock controls.")