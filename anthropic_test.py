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

import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Client(ANTHROPIC_API_KEY)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Client(ANTHROPIC_API_KEY)

def read_file(file_path):
    file_type = magic.from_file(file_path)
    print(file_type)
    if "text" in file_type or file_path.endswith(".py"):
        with open(file_path, 'r') as f:
            file_contents = f.read()
    elif "PDF" in file_type:
        with open(file_path, 'rb') as f:
            pdf = PdfFileReader(f)
            file_contents = "\n".join(page.extract_text() for page in pdf.pages)
    elif "Microsoft Word" in file_type:
        doc = Document(file_path)
        file_contents = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif "Excel" in file_type:
        df = pd.read_excel(file_path)
        file_contents = df.to_string()
    elif "HTML" in file_type:
        with open(file_path, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
            file_contents = soup.get_text()
    elif "image" in file_type:
        file_contents = pytesseract.image_to_string(file_path)
    elif "PowerPoint" in file_type:
        pres = Presentation(file_path)
        file_contents = "\n".join(slide.text for slide in pres.slides)
    elif "Rich Text Format" in file_type:
        with open(file_path, 'r') as f:
            file_contents = rtf_to_text(f.read())
    elif "CSV" in file_type:
        df = pd.read_csv(file_path)
        file_contents = df.to_string()
    else:
        raise Exception(f"Unsupported file type. The file must be a text file, but a {file_type} file was provided.")

    return file_contents, file_type

def write_prompt_to_text_file(prompt):
    with open("prompt.txt", "w") as f:
        f.write(prompt)

def generate_response(document, question, history, file_type):
    prompt = f"{history}This document is of type {file_type}. \n<document>\n{document}\n</document>\nHere is the first question: {question}\n"
    write_prompt_to_text_file(prompt)
    response = client.completion(
        prompt=f"{anthropic.HUMAN_PROMPT}{prompt}{anthropic.AI_PROMPT}",
        stop_sequences = [anthropic.HUMAN_PROMPT],
        model="claude-v1",
        max_tokens_to_sample=100,
    )
    return response['completion']


if __name__ == "__main__":
    file_path = input("Enter the file path: ")
    document, file_type = read_file(file_path)
    history = ""
    while True:
        question = input("Enter your question: ")
        try:
            answer = generate_response(document, question, history, file_type)
            print(answer)
            history += f"Human: {question}\nAssistant: {answer}\n"
        except Exception as e:
            print(f"An error occurred: {e}")


