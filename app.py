import os
import pandas as pd
import magic
from dotenv import load_dotenv
from rich import print
from PyPDF2 import PdfFileReader
from docx import Document
from bs4 import BeautifulSoup
import pytesseract
from pptx import Presentation
from striprtf.striprtf import rtf_to_text
import streamlit as st

import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Client(ANTHROPIC_API_KEY)

def read_file(file):
    file_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    if "text" in file_type or file.name.endswith(".py"):
        file_contents = file.read().decode()
    elif "pdf" in file_type:
        pdf = PdfFileReader(file)
        file_contents = "\n".join(page.extract_text() for page in pdf.pages)
    elif "msword" in file_type or "officedocument.wordprocessingml.document" in file_type:
        doc = Document(file)
        file_contents = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif "excel" in file_type:
        df = pd.read_excel(file)
        file_contents = df.to_string()
    elif "html" in file_type:
        soup = BeautifulSoup(file, 'html.parser')
        file_contents = soup.get_text()
    elif "image" in file_type:
        file_contents = pytesseract.image_to_string(file)
    elif "powerpoint" in file_type:
        pres = Presentation(file)
        file_contents = "\n".join(slide.text for slide in pres.slides)
    elif "rtf" in file_type:
        file_contents = rtf_to_text(file.read().decode())
    elif "csv" in file_type:
        df = pd.read_csv(file)
        file_contents = df.to_string()
    else:
        raise Exception(f"Unsupported file type. The file must be a text file, but a {file_type} file was provided.")

    return file_contents, file_type

def generate_response(document, question, history, file_type):
    prompt = f"{history}This document is of type {file_type}. \n<document>\n{document}\n</document>\nHere is the first question: {question}\n"
    response = client.completion(
        prompt=f"{anthropic.HUMAN_PROMPT}{prompt}{anthropic.AI_PROMPT}",
        stop_sequences = [anthropic.HUMAN_PROMPT],
        model="claude-v1",
        max_tokens_to_sample=100,
    )
    return response['completion']

st.title("Document Analyzer")

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    document, file_type = read_file(uploaded_file)
    history = ""
    while True:
        question = st.text_input("Enter your question: ")
        if question:
            try:
                answer = generate_response(document, question, history, file_type)
                st.write(f"Answer: {answer}")
                history += f"Human: {question}\nAssistant: {answer}\n"
            except Exception as e:
                st.write(f"An error occurred: {e}")
