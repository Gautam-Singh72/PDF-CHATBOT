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

# embedding this chunks and storing them in a vector store :
def get_vectore_store(text_chunks, model_name, api_key=None):
    if model_name=="Google AI":
        embeddings=GoogleGenerativeAIEmbeddings(model='model/embedding-001', google_api_key=api_key)
    vectore_store=FAISS.from_texts(text_chunks, embedding=embeddings)
    vectore_store.save_local("faiss_index")
    return vectore_store

#create a conversational chain using langchain
def get_conversational_chain(model_name, vectorstore=None, api_key=None):
    if model_name=="Google AI":
        prompt_template="""
               Answer the question in a clear and concise way from the provided context, make sure to provide
               all details with proper structure, if the answer is not in the provided context just say, "answer
               is not available in the context", don't provide the wrong answer.\n\n 
               context:\n {context}?\n
               Question:\n {question}?\n

               Answer:    
            """
        model= ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3, google_api_key=api_key)
        prompt=PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain=load_qa_chain(model, chain_type="stuff", prompt=prompt)

# take user input
def user_input(user_question, model_name, api_key, pdf_docs, conversation_history):
    if api_key is None or pdf_docs is None:
        st.warning("please upload any pdf and valid api key")
        return
    text_chunks=get_text_chunks(get_pdf_text(pdf_docs), model_name)
    vector_store=get_vectore_store(text_chunks, model_name, api_key)
    user_question_output=""
    response_output=""
    if model_name=="Google AI":
        embeddings=GoogleGenerativeAIEmbeddings(model='model/embedding-001', google_api_key=api_key)
        new_db=FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs=new_db.similarity_search(user_question)
        chain=get_conversational_chain("Google AI", vectorstore=new_db, api_key=api_key)
        response=chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        user_question_output=user_question
        response_output=response['output_text']
        pdf_names=[pdf.name for pdf in pdf_docs] if pdf_docs else []
        conversation_history.append((user_question_output, response_output, model_name, datetime.now().strftime
        ('%Y-%m-%d %H:%M:%S'),",".join(pdf_names)))

    st.markdown(
        f"""
        <style>
            .chat-message {{
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                display: flex;
            }}
            .chat-message.user {{
                background-color: #2b313e;
            }}
            .chat-message.bot {{
                background-color: #475063;
            }}
            .chat-message .avatar {{
                width: 20%;
            }}
            .chat-message .avatar img {{
                max-width: 78px;
                max-height: 78px;
                border-radius: 50%;
                object-fit: cover;
            }}
            .chat-message .message {{
                width: 80%;
                padding: 0 1.5rem;
                color: #fff;
            }}
            .chat-message .info {{
                font-size: 0.8rem;
                margin-top: 0.5rem;
                color: #ccc;
            }}
        </style>
        <div class="chat-message user">
            <div class="avatar">
                <img src="https://i.ibb.co/CKpTnWr/user-icon-2048x2048-ihoxz4vq.png">
            </div>    
            <div class="message">{user_question_output}</div>
        </div>
        <div class="chat-message bot">
            <div class="avatar">
                <img src="https://i.ibb.co/wNmYHsx/langchain-logo.webp" >
            </div>
            <div class="message">{response_output}</div>
            </div>
            
        """,
        unsafe_allow_html=True
    )

    # <div class="info" style="margin-left: 20px;">Timestamp: {datetime.now()}</div>
    # <div class="info" style="margin-left: 20px;">PDF Name: {", ".join(pdf_names)}</div>
    if len(conversation_history) == 1:
        conversation_history = []
    elif len(conversation_history) > 1 :
        last_item = conversation_history[-1]  
        conversation_history.remove(last_item) 
    for question, answer, model_name, timestamp, pdf_name in reversed(conversation_history):
        st.markdown(
            f"""
            <div class="chat-message user">
                <div class="avatar">
                    <img src="https://i.ibb.co/CKpTnWr/user-icon-2048x2048-ihoxz4vq.png">
                </div>    
                <div class="message">{question}</div>
            </div>
            <div class="chat-message bot">
                <div class="avatar">
                    <img src="https://i.ibb.co/wNmYHsx/langchain-logo.webp" >
                </div>
                <div class="message">{answer}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if len(st.session_state.conversation_history) > 0:
        df = pd.DataFrame(st.session_state.conversation_history, columns=["Question", "Answer", "Model", "Timestamp", "PDF Name"])

        # df = pd.DataFrame(st.session_state.conversation_history, columns=["Question", "Answer", "Timestamp", "PDF Name"])
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # Convert to base64
        href = f'<a href="data:file/csv;base64,{b64}" download="conversation_history.csv"><button>Download conversation history as CSV file</button></a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)
        st.markdown("To download the conversation, click the Download button on the left side at the bottom of the conversation.")
    st.snow()
