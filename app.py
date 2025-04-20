# Configuration (add at top after imports)
warnings.filterwarnings(
    "ignore",
    message="builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute",
    category=DeprecationWarning
)

# Streamlit Cloud-specific Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'

import os
import tempfile
import warnings
from typing import List, Optional

import fitz  # PyMuPDF
import pytesseract
import streamlit as st
from markitdown import MarkItDown
from openai import OpenAI
from PIL import Image


def streamlit_ocr(image):
    """Optimized OCR function for Streamlit Cloud"""
    try:
        return pytesseract.image_to_string(image, lang='eng')
    except Exception as e:
        st.error(f"OCR Failed: {str(e)}")
        st.info("This usually means Tesseract isn't properly installed in the container")
        return ""

# Streamlit UI
st.title("OCR in Streamlit Cloud")
upload = st.file_uploader("Upload image", type=["png","jpg","jpeg"])

if upload:
    img = Image.open(upload)
    st.image(img, caption="Uploaded Image")
    
    if st.button("Extract Text"):
        text = streamlit_ocr(img)
        st.text_area("Extracted Text", text, height=200)


# Initialize app
st.set_page_config(page_title="🧠 AI File Chat", layout="centered")
st.title("🧠 Content Extraction")

# Initialize OpenAI client
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OpenAI API key not found in secrets!")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
LLM_MODEL = "gpt-4.1-mini"

# --- Core Functions (kept same as original) ---
def pdf_to_images(file_obj, dpi: int = 300) -> List[Image.Image]:
    """Convert PDF to list of PIL Images"""
    try:
        if isinstance(file_obj, str):
            doc = fitz.open(file_obj)
        else:
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")
        
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=dpi, colorspace="rgb")
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        return pages
    except Exception as e:
        st.error(f"PDF processing error: {str(e)}")
        return []
    finally:
        if 'doc' in locals():
            doc.close()

def convert_file(path: str) -> Optional[str]:
    """Convert file to text using MarkItDown or OCR fallback"""
    ext = os.path.splitext(path)[1].lower()
    
    # Try MarkItDown first
    try:
        with st.spinner("Extracting structured text..."):
            md = MarkItDown(enable_plugins=False)
            result = md.convert(path)
            if result.text_content.strip():
                return result.text_content
    except Exception:
        pass  # Silent fallback to OCR
    
    # Fallback to OCR
    with st.spinner("Running OCR..."):
        try:
            if ext == '.pdf':
                pages = pdf_to_images(path)
            elif ext in ['.jpg', '.jpeg', '.png']:
                pages = [Image.open(path)]
            else:
                st.error(f"Unsupported file format: {ext}")
                return None
            
            return "\n".join(pytesseract.image_to_string(img, lang='eng') for img in pages)
        except Exception as e:
            st.error(f"OCR failed: {str(e)}")
            return None

def reorganize_markdown(raw: str) -> Optional[str]:
    """Reorganize content using OpenAI"""
    with st.spinner("Improving structure..."):
        try:
            completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "user", "content": f"reorganize:\n{raw}"},
                    {"role": "system", "content": "Reorganize this content in Markdown without adding or removing content."}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"Reorganization failed: {str(e)}")
            return None

def rag(content: str, question: str) -> Optional[str]:
    """Answer questions using RAG"""
    with st.spinner("Generating answer..."):
        try:
            completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "user", "content": question},
                    {"role": "system", "content": f"Answer from this content:\n{content}"}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
            return None

# --- UI Components ---
def sidebar():
    with st.sidebar:
        st.image("formal_image.jpg", width=150) if os.path.exists("formal_image.jpg") else None
        st.write("### Implemented By:")
        st.write("**Eng.Ahmed Zeyad Tareq**")
        st.write("📌 Data Scientist | 🎓 Master of AI Engineering")
        st.write("[📷 Instagram](https://www.instagram.com/adlm7) | "
                "[🔗 LinkedIn](https://www.linkedin.com/in/ahmed-zeyad-tareq) | "
                "[🐙 GitHub](https://github.com/AhmedZeyadTareq)")

def main():
    sidebar()
    
    uploaded_file = st.file_uploader(
        "📂 Choose File:", 
        type=["pdf", "txt", "jpg", "png", "jpeg"],
        help="Supported formats: PDF, TXT, JPG, PNG"
    )
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.read())
            file_path = tmp_file.name
            
            if st.button("Start Processing 🔁"):
                if raw_text := convert_file(file_path):
                    st.text_area("📄 Extracted Content:", raw_text, height=200)
                    st.session_state.raw_text = raw_text
            
            if "raw_text" in st.session_state:
                if st.button("🧹 Reorganize Content"):
                    if organized := reorganize_markdown(st.session_state.raw_text):
                        st.session_state.organized_text = organized
                        st.markdown(organized)
                
                if "organized_text" in st.session_state:
                    st.download_button(
                        "⬇️ Download Organized File",
                        data=st.session_state.organized_text,
                        file_name="organized.md",
                        mime="text/markdown"
                    )
                    
                    st.divider()
                    question = st.text_input("Ask about the content ❓")
                    if question and st.button("💬 Get Answer"):
                        if answer := rag(st.session_state.organized_text, question):
                            st.markdown(f"**Answer:** {answer}")

if __name__ == "__main__":
    main()
