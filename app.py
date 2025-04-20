
from openai import OpenAI
from llama_parse import LlamaParse
import os
import streamlit as st
import tempfile
from PIL import Image


LLM_MODEL = "gpt-4.1-mini"

openkey = st.secrets["OPENAI_API_KEY"]
llamakey = st.secrets["LLAMA_API_KEY"]


st.set_page_config(page_title="🧠 AI File Chat", layout="centered")
st.title("🧠 Content Extraction")


uploaded_file = st.file_uploader("📂 Choose File:", type=["pdf", "txt", "jpg", "png"])


def parsing(uploaded_file):
    try:
        # Save the uploaded file to a temporary file
        suffix = os.path.splitext(uploaded_file.name)[1]  # Get file extension (.pdf, .txt, etc.)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name  # Get the path of the saved file

        # Initialize the parser
        parser = LlamaParse(api_key=LLAMA_API_KEY, result_type="markdown")

        # Parse the file using its path
        documents = parser.load_data(tmp_file_path)

        # Clean up: Delete the temporary file after parsing
        os.unlink(tmp_file_path)  # Remove the temp file

        if not documents:
            st.error("Failed to parse the document - no content returned")
            return ""

        return documents[0].text

    except Exception as e:
        st.error(f"Error parsing document: {str(e)}")
        return ""


def rag(content, question):
    client = OpenAI()
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"Give me Direct Answer: {question}"
            },
            {
                "role": "system",
                "content": f"you are an assistant answer directly and concise from the following content:\n {content}"
            }
        ]
    )
    return completion.choices[0].message.content





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

if uploaded_file:
    # grab the real extension (".pdf", ".jpg", etc.)
    suffix = os.path.splitext(uploaded_file.name)[1]
    with (tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file):
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

        if st.button("Start 🔁"):
            raw_text = parsing(uploaded_file)
            st.text_area("📄 Content:", raw_text, height=200)
            st.session_state["raw_text"] = raw_text
            # Add a download button for the reorganized text
            st.download_button(
                label="⬇️ Download as TXT",
                data=raw_text,
                file_name="reorganized_content.txt",
                mime="text/plain",
                key="download_txt")  # Unique key to avoid conflicts

        if "raw_text" in st.session_state:
            if st.button("Show.."):
                st.text_area("📄 Content:", st.session_state["raw_text"], height=200)

        if "raw_text" in st.session_state:
            question = st.text_input(" Ask Anything about Content..❓")
            if st.button("💬 Send"):
                answer = rag(st.session_state["raw_text"], question)
                st.markdown(f"**Question❓:**\n{question}")
                st.markdown(f"**Answer💡:**\n{answer}")





#PERFECTO
