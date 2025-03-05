import zipfile
import os
import shutil
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
    # Clear previous zip file if it exists
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    extract_path = "extracted_pdfs"
    # Clear previous extraction folder if it exists
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Inform the user if there are internal folders
    internal_folders = [f for f in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, f))]
    if internal_folders:
        st.info(f"Internal folders detected: {internal_folders}. Processing PDFs within these folders.")

    # Function to extract text from a single PDF file
    def extract_text_from_pdf(pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            st.error(f"Error processing {pdf_path}: {e}")
        return text

    # Extract text from all PDFs and store in a dictionary {filename: text}
    pdf_texts = {}
    for root, _, files in os.walk(extract_path):
        for filename in files:
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, filename)
                file_text = extract_text_from_pdf(pdf_path)
                if file_text.strip():
                    pdf_texts[filename] = file_text

    if not pdf_texts:
        st.error("No text extracted from any PDFs. Please upload valid documents.")
    else:
        st.success("PDFs extracted and processed successfully!")
        
        # Let the user select a specific PDF from the extracted files
        selected_pdf = st.selectbox("Select a PDF to work with", options=list(pdf_texts.keys()))
        selected_text = pdf_texts.get(selected_pdf, "")

        # Summarization Function for a single PDF
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
            summary = summarize_text(selected_text)
            st.subheader(f"Summary of {selected_pdf}:")
            st.write(summary)
        
        # Q&A Section for the selected PDF
        st.subheader("Ask Questions Based on the Selected PDF")
        user_question = st.text_input("Enter your question:")
        
        def ask_question(question, text):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant that answers questions based on the given document."},
                    {"role": "user", "content": f"Based on this document, answer: {question}\n{text[:4096]}"}
                ]
            )
            return response.choices[0].message.content
        
        if user_question:
            answer = ask_question(user_question, selected_text)
            st.subheader("Answer:")
            st.write(answer)
