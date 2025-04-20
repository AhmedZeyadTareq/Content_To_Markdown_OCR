import streamlit as st
import os
import tempfile
import io
import sys
from markitdown import MarkItDown
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from openai import OpenAI

# إعدادات عامة
api_key = st.secrets["OPENAI_API_KEY"]
LLM_MODEL = "gpt-4.1"
st.set_page_config(page_title="🧠 AI File Chat", layout="centered")
st.title("🧠 Content Extraction")

# الشريط الجانبي
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

# page = st.sidebar.radio("Choose Task:", ["Derive", "RAG"])

# uploader
uploaded_file = st.file_uploader("📤 Choose File:", type=["pdf", "txt", "jpg", "png"])

# system function
def capture_print_output(func, *args, **kwargs):
    buffer = io.StringIO()
    sys.stdout = buffer
    try:
        result = func(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = sys.__stdout__
    return result, output

def convert_file(path: str) -> str:
    try:
        print("🧪 Extraction Processing...")
        md = MarkItDown(enable_plugins=False)
        result = md.convert(path)
        if result.text_content.strip():
            with open('converted.md', 'w', encoding='utf-8') as f:
                f.write(result.text_content)
            print("✅ Done.. Content Extracted")
            return result.text_content
        else:
            print("⚠️ NO Content, OCR Activated >>>")
    except:
        print("❌ Failed - OCR Activated >>> ")

    ext = os.path.splitext(path)[1].lower()
    pages = []

    if ext == ".pdf":
        try:
            pages = convert_from_path(path)
        except Exception as e:
            print(f"❌ Failed to process PDF: {e}")
            return "❌ Failed to process PDF file."
    elif ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(path)
            pages = [img]
        except Exception as e:
            print(f"❌ Invalid image: {e}")
            return "❌ Invalid image file."
    else:
        print("❌ Unsupported file format.")
        return "❌ Unsupported file format."

    # إذا وصلنا هنا معناها الصورة أو PDF تم فتحها بنجاح
    full_text = ""
    for img in pages:
        text = pytesseract.image_to_string(img, lang='eng')
        full_text += "\n" + text

    if full_text.strip():
        print("✅ OCR Done Successfully.")
        return full_text
    else:
        print("⚠️ OCR finished but no readable text found.")
        return "⚠️ OCR finished but no readable text found."


def reorganize_markdown(raw: str) -> str:
    client = OpenAI(api_key=api_key)
    chat = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": f"reorganize the following content:\n{raw}"},
            {"role": "system", "content": "Respond with improved markdown only. DO NO start response with (```markdown). start with the content directly"}
        ]
    )
    content = chat.choices[0].message.content
    with open("organized.md", "w", encoding="utf-8") as f:
        f.write(content)
    return content

def rag(content, question):
    client = OpenAI(api_key=api_key)
    chat = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": question},
            {"role": "system", "content": f"Answer directly, very specific and concise from the following content:\n{content}"}
        ]
    )
    return chat.choices[0].message.content

# UI implementation
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    if st.button("Start 🔁"):
        result_text, logs = capture_print_output(convert_file, file_path)
        st.text_area("📄 Content:", result_text, height=200)

        st.session_state["result_text"] = result_text

    if "result_text" in st.session_state:
        if st.button("🧹 Reorganize to Content"):
            organized = reorganize_markdown(st.session_state["result_text"])
            st.session_state["organized_text"] = organized
            # st.markdown("📘 **Content Reorganized:**", unsafe_allow_html=True)
            # st.markdown(organized, unsafe_allow_html=True)
            st.write("📄 Reorganized Content:\n", organized)
        if "organized_text" in st.session_state:
            with open("organized.md", "rb") as f:
                st.download_button("⬇️ Download File", f, file_name="organized.md")

            question = st.text_input(" Ask Anything about Content..❓")
            if st.button("💬 Send"):
                answer = rag(st.session_state["organized_text"], question)
                st.markdown(f"**Question❓:**\n{question}")
                st.markdown(f"**Answer💡:**\n{answer}")

# streamlit run ready_openai_simple_UI.py
