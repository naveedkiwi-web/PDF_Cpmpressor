import streamlit as st
import subprocess
import os
import shutil

# --- Configuration ---
# Set the max upload size for Streamlit (2GB in MB)
# Note: This config is usually set in .streamlit/config.toml, 
# but we handle the logic here.
st.set_page_config(page_title="PDF Compressor", layout="centered")

def compress_pdf(input_path, output_path, power):
    """
    Compresses PDF using Ghostscript.
    
    levels:
    0: default - almost identical to /screen
    1: prepress - high quality, color preserving, 300 dpi imgs
    2: printer - high quality, 300 dpi images
    3: ebook - medium quality, 150 dpi images
    4: screen - screen-view-only quality, 72 dpi images
    """
    
    # Mapping your UI settings to Ghostscript settings
    quality = {
        "High (average quality)": "/screen",   # Max compression
        "Medium (good quality)": "/ebook",     # Balanced
        "Low (best quality)": "/printer",      # Minimal compression
    }

    gs_setting = quality.get(power, "/default")

    # The Ghostscript command
    command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Compression failed: {e}")
        return False

# --- UI Interface ---
st.title("Compress")

# 1. File Upload
uploaded_file = st.file_uploader("Upload a document", type=['pdf'])

# 2. Compression Settings (Matching your image)
st.subheader("Compression level")

compression_options = [
    "Medium (good quality)",
    "No Compression",
    "High (average quality)",
    "Low (best quality)"
]

# Default index 0 is Medium
option = st.selectbox(
    "Select the desired compression level:",
    compression_options,
    index=0
)

# Show the helper text based on your image
st.caption(
    "Select the desired compression level: "
    "No Compression for original quality, "
    "High for maximum compression and smaller size, "
    "Medium for a balance between quality and size, "
    "or Low for minimal compression and higher quality."
)

if uploaded_file is not None:
    # Display file details
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.write(f"**Original File Name:** {uploaded_file.name}")
    st.write(f"**Original Size:** {file_size_mb:.2f} MB")

    if st.button("Compress PDF"):
        if option == "No Compression":
            st.warning("You selected 'No Compression'. Please select a level to compress.")
        else:
            with st.spinner("Compressing... (Large files may take time)"):
                # Create a temporary directory
                if not os.path.exists("temp"):
                    os.makedirs("temp")
                
                input_path = os.path.join("temp", "input.pdf")
                output_path = os.path.join("temp", f"compressed_{uploaded_file.name}")

                # Save uploaded file to disk (Chunked write to handle large files)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Run Compression
                success = compress_pdf(input_path, output_path, option)

                if success:
                    # Get new size
                    new_size = os.path.getsize(output_path) / (1024 * 1024)
                    reduction = ((file_size_mb - new_size) / file_size_mb) * 100
                    
                    st.success(f"Done! File compressed by {reduction:.1f}%")
                    st.write(f"**New Size:** {new_size:.2f} MB")

                    # Download Button
                    with open(output_path, "rb") as file:
                        btn = st.download_button(
                            label="Download Compressed PDF",
                            data=file,
                            file_name=f"compressed_{uploaded_file.name}",
                            mime="application/pdf"
                        )
                
                # Cleanup temp files (Optional: Streamlit cleans up on restart, but good practice)
                # shutil.rmtree("temp")