from markitdown import MarkItDown
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import os
from openai import OpenAI
import streamlit as st
import tempfile
import warnings

# Configure Tesseract path for different environments
tesseract_paths = [
    '/usr/bin/tesseract',       # Streamlit Cloud/Linux
    '/usr/local/bin/tesseract', # Alternative Linux path
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
]

for path in tesseract_paths:
    try:
        pytesseract.pytesseract.tesseract_cmd = path
        break
    except Exception:
        continue

# Suppress warnings
warnings.filterwarnings(
    "ignore",
    message="builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute",
    category=DeprecationWarning
)

# App Config
st.set_page_config(page_title="🧠 AI File Chat", layout="centered")
st.title("🧠 Content Extraction")

# Initialize OpenAI client
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found in secrets!")
    st.stop()

client = OpenAI(api_key=api_key)
LLM_MODEL = "gpt-4.1-mini"  # Updated to current recommended model

# Sidebar with logo and description
def create_sidebar():
    with st.sidebar:
        logo_link = "formal_image.jpg"
        if os.path.exists(logo_link):
            try:
                logo_image = Image.open(logo_link)
                st.image(logo_image, width=150)
            except Exception as e:
                st.warning(f"Could not load logo: {e}")

        st.write("### Implemented By:")
        st.write("**Eng.Ahmed Zeyad Tareq**")
        st.write("📌 Data Scientist.")
        st.write("🎓 Master of AI Engineering.")
        st.write("📷 Instagram: [@adlm7](https://www.instagram.com/adlm7)")
        st.write("🔗 LinkedIn: [Ahmed Zeyad Tareq](https://www.linkedin.com/in/ahmed-zeyad-tareq)")
        st.write("🔗 Github: [Ahmed Zeyad Tareq](https://github.com/AhmedZeyadTareq)")
        st.write("🔗 Kaggle: [Ahmed Zeyad Tareq](https://www.kaggle.com/ahmedzeyadtareq)")

# File processing functions
def pdf_to_images(file_obj, dpi: int = 300) -> list[Image.Image]:
    """Convert PDF to list of PIL Images, handling both file paths and file objects"""
    try:
        if isinstance(file_obj, str):
            doc = fitz.open(file_obj)  # File path
        else:
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")  # File object
        
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=dpi, colorspace="rgb")
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        return pages
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return []
    finally:
        if 'doc' in locals():
            doc.close()

def convert_file(path: str) -> str:
    """Convert file to text using MarkItDown first, then fallback to OCR"""
    ext = os.path.splitext(path)[1].lower()
    
    # Try MarkItDown first
    try:
        with st.spinner("Trying structured text extraction..."):
            md = MarkItDown(enable_plugins=False)
            result = md.convert(path)
            if result.text_content.strip():
                return result.text_content
    except Exception as e:
        st.warning(f"MarkItDown extraction failed: {e}")
    
    # Fallback to OCR
    with st.spinner("Running OCR..."):
        try:
            if ext == '.pdf':
                pages = pdf_to_images(path, dpi=300)
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                pages = [Image.open(path)]
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            full_text = ""
            for img in pages:
                page_text = pytesseract.image_to_string(img, lang='eng')
                full_text += "\n" + page_text
            
            return full_text
        except Exception as e:
            st.error(f"OCR processing failed: {e}")
            return ""

def reorganize_markdown(raw: str) -> str:
    """Reorganize content using OpenAI"""
    with st.spinner("Reorganizing content..."):
        try:
            completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "user", "content": f"reorganize the following content:\n{raw}"},
                    {"role": "system", "content": """You are a reorganizer. Return the content in Markdown, keeping it identical. 
                        Do not delete or replace anything—only reorganize it for better structure. 
                        Respond with only the reorganized content, without any additional words or symbols."""}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI reorganization failed: {e}")
            return raw

def rag(con, qu):
    """Answer questions using RAG"""
    with st.spinner("Generating answer..."):
        try:
            completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "user", "content": qu},
                    {"role": "system", "content": f"""You are an assistant. Answer directly and concisely from the following content.
                        If the answer isn't in the content, say "I couldn't find this information in the document."\n\n{con}"""}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI query failed: {e}")
            return "Sorry, I couldn't process your question."

# Main app
def main():
    create_sidebar()
    
    uploaded_file = st.file_uploader(
        "📂 Choose File:", 
        type=["pdf", "txt", "jpg", "png", "jpeg"],
        help="Supported formats: PDF, TXT, JPG, PNG"
    )
    
    if uploaded_file:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            file_path = tmp_file.name
            
            if st.button("Start Processing 🔁"):
                raw_text = convert_file(file_path)
                st.text_area("📄 Extracted Content:", raw_text, height=200)
                st.session_state["raw_text"] = raw_text
            
            if "raw_text" in st.session_state:
                if st.button("🧹 Reorganize Content"):
                    organized = reorganize_markdown(st.session_state["raw_text"])
                    st.session_state["organized_text"] = organized
                    st.markdown(organized)
                
                if "organized_text" in st.session_state:
                    # Create download button
                    organized_md = st.session_state["organized_text"]
                    st.download_button(
                        "⬇️ Download Organized File",
                        data=organized_md,
                        file_name="organized_content.md",
                        mime="text/markdown"
                    )
                    
                    # Question answering
                    st.divider()
                    question = st.text_input("Ask anything about the content ❓")
                    if st.button("💬 Get Answer"):
                        if question.strip():
                            answer = rag(st.session_state["organized_text"], question)
                            st.markdown(f"**Question:** {question}")
                            st.markdown(f"**Answer:** {answer}")
                        else:
                            st.warning("Please enter a question")

if __name__ == "__main__":
    main()
