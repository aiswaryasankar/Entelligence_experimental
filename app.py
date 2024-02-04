import streamlit as st
import requests
#from openai import OpenAI


st.title("👩‍🏫AI Mentor for AI Engineers")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = "sample response"
        #stream = #generate response here, enable stream
        #response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})