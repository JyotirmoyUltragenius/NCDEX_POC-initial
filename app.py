import zipfile
import os
import PyPDF2
import openai
import streamlit as st

# Streamlit UI
st.title("NCDEX Q&A Assistant")

# Get OpenAI API Key from Environment Variable
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("API key not found. Please set the API_KEY environment variable.")
else:
    openai.api_key = api_key

# File Upload
uploaded_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"])

if uploaded_file:
    zip_path = "uploaded.zip"
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    extract_path = "extracted_pdfs"
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Check for internal folders
    internal_folders = [f for f in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, f))]
    if internal_folders:
        st.info(f"Internal folders detected: {internal_folders}. Processing PDFs within these folders.")

    # Extract text from PDFs
    def extract_text_from_pdfs(directory):
        pdf_texts = ""
        # os.walk recursively traverses the directory structure, handling internal folders
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, filename)
                    try:
                        with open(pdf_path, "rb") as pdf_file:
                            reader = PyPDF2.PdfReader(pdf_file)
                            for page in reader.pages:
                                text = page.extract_text()
                                if text:
                                    pdf_texts += text + "\n"
                    except Exception as e:
                        st.error(f"Error processing {pdf_path}: {e}")
        return pdf_texts

    pdf_text = extract_text_from_pdfs(extract_path)
    
    if not pdf_text.strip():
        st.error("No text extracted from the PDFs. Please upload valid documents.")
    else:
        st.success("PDFs extracted and processed successfully!")
        
        # Summarization Function
        def summarize_text(text):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant that summarizes compliance regulations for NCDEX. Read and analyze these documents carefully."},
                    {"role": "user", "content": f"Summarize this document:\n{text[:4096]}"}
                ]
            )
            return response.choices[0].message.content
        
        if st.button("Generate Summary"):
            summary = summarize_text(pdf_text)
            st.subheader("Summary of PDFs:")
            st.write(summary)
        
        # Q&A Section
        st.subheader("Ask Questions Based on the PDFs")
        user_question = st.text_input("Enter your question:")
        
        def ask_question(question, text):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant that answers questions based on the given documents."},
                    {"role": "user", "content": f"Based on this document, answer: {question}\n{text[:4096]}"}
                ]
            )
            return response.choices[0].message.content
        
        if user_question:
            answer = ask_question(user_question, pdf_text)
            st.subheader("Answer:")
            st.write(answer)
