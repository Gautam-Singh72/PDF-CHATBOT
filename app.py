# import packages :

import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
import base64

import os
#imports for langchain :

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate

from datetime import datetime

# to get text from pdf

def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text
    return text

#to get chunks from text:
def get_text_chunks(text, model_name):
    if model_name=="Google AI":
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=700)
    chunks=text_splitter.split_text(text)
    return chunks

