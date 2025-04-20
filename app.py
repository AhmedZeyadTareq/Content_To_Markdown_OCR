from markitdown import MarkItDown
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import os
from openai import OpenAI
import tiktoken

import streamlit as st
import tempfile


# Confige
api_key = st.secrets["OPENAI_API_KEY"]
LLM_MODEL = "gpt-4.1-mini"


import warnings
warnings.filterwarnings("ignore",
    message="builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute",
    category=DeprecationWarning)



st.set_page_config(page_title="🧠 AI File Chat", layout="centered")
st.title("🧠 Content Extraction")


# side bar
logo_link = "formal image.jpg"
# Sidebar with logo and description
with st.sidebar:
    if os.path.exists(logo_link):
        logo_image = Image.open(logo_link)
        st.image(logo_image, width=150)  # Adjust width as needed
    else:
        st.warning("Logo not found. Please check the logo path.")

    st.write("### Implemented By:")
    st.write("**Eng.Ahmed Zeyad Tareq**")
    st.write("📌 Data Scientist.")
    st.write("🎓 Master of AI Engineering.")
    st.write("📷 Instagram: [@adlm7](https://www.instagram.com/adlm7)")
    st.write("🔗 LinkedIn: [Ahmed Zeyad Tareq](https://www.linkedin.com/in/ahmed-zeyad-tareq)")
    st.write("🔗 Github: [Ahmed Zeyad Tareq](https://github.com/AhmedZeyadTareq)")
    st.write("🔗 Kaggle: [Ahmed Zeyad Tareq](https://www.kaggle.com/ahmedzeyadtareq)")
#
#
uploaded_file = st.file_uploader("📂 Choose File:", type=["pdf", "txt", "jpg", "png"])


def pdf_to_images(file_obj, dpi: int = 300) -> list[Image.Image]:
    """Handle both file paths and file objects"""
    if isinstance(file_obj, str):
        # Regular file path
        doc = fitz.open(file_obj)
    else:
        # File-like object (Streamlit case)
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")

    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi, colorspace="rgb")
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(img)
    doc.close()
    return pages


# ---- File → Text (MarkItDown → OCR) ----
def convert_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        print("[🔍] Trying structured text extraction via MarkItDown.....")
        md = MarkItDown(enable_plugins=False)
        result = md.convert(path)
        if result.text_content.strip():
            print(f"[✔]=== Markdown Derived ===\n Now Model Reorganizing.....")
            with open('data.md', 'a', encoding='utf-8') as f:
                f.write(result.text_content)
                print("===Reorganized Saved, DONE===\n")
            return result.text_content
        else:
            print("[⚠️] No text found via MarkItDown, falling back to OCR...")
    except Exception:
        print(f"[❌] MarkItDown failed")
        print("[🔁] Falling back to OCR...")

    # Fallback OCR
    print("[🔍]===OCR Started.......")
    try:
        _ = fitz.open(path)
        is_pdf = True
    except Exception:
        is_pdf = False

    if is_pdf:
        pages = pdf_to_images(path, dpi=300)
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        pages = [Image.open(path)]
    else:
        raise Exception(f"Unsupported file format: {ext or 'unknown'}")

    # 3b) run Tesseract on each image page
    full_text = ""
    for img in pages:
        page_text = pytesseract.image_to_string(img, lang='eng')
        full_text += "\n" + page_text

    return full_text


# ---- Markdown Reorganization via OpenAI ----
def reorganize_markdown(raw: str) -> str:
    client = OpenAI()

    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"reorganize the following content:\n {raw}"
            },
            {
                "role": "system",
                "content": f"You are a reorganizer. Return the content in Markdown, keeping it identical. Do not delete\
                 or replace anything—only reorganize it for better structure. Respond with only the reorganized content,\
                  without any additional words or symbols (''')."
            }
        ]
    )
    with open('data.md', 'a', encoding='utf-8') as f:
        f.write(completion.choices[0].message.content)
        print("===Reorganized Saved, DONE===\n")
    return completion.choices[0].message.content


# ---- Build RAG QA Chain ----
def rag(con, qu):
    client = OpenAI()

    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": qu
            },
            {
                "role": "system",
                "content": f"you are an assistant answer directly and concise from the following content:\n {con}"
            }
        ]
    )
    return completion.choices[0].message.content

def count_tokens(content, model="gpt-4-turbo"):  # Use your model name
    enc = tiktoken.encoding_for_model(model)
    print(f"The Size of the Content_Tokens: {len(enc.encode(content))}")


if uploaded_file:
    # grab the real extension (".pdf", ".jpg", etc.)
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

        if st.button("Start 🔁"):
            raw_text = convert_file(file_path)
            st.text_area("📄 Content:", raw_text, height=200)
            st.session_state["raw_text"] = raw_text

        if "raw_text" in st.session_state:
            if st.button("🧹 Reorganize to Content"):
                organized = reorganize_markdown(st.session_state["raw_text"])
                st.session_state["organized_text"] = organized
                st.markdown(organized)
            if "organized_text" in st.session_state:
                with open("organized.md", "rb") as f:
                    st.download_button("⬇️ Download File", f, file_name="organized.md")

                question = st.text_input(" Ask Anything about Content..❓")
                if st.button("💬 Send"):
                    answer = rag(st.session_state["organized_text"], question)
                    st.markdown(f"**Question❓:**\n{question}")
                    st.markdown(f"**Answer💡:**\n{answer}")

