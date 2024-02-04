import streamlit as st
import requests
from openai import OpenAI
from router import create_agent


header = st.container()
header.title("👩‍🏫AI Mentor for AI Engineers")
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

### Custom CSS for the sticky header
st.markdown(
    """
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 2.875rem;
        background-color: #121212;
        z-index: 999;
    }
    .fixed-header {
    background-color: #121212;
    }
</style>
    """,
    unsafe_allow_html=True
)
#st.title("👩‍🏫AI Mentor for AI Engineers")

# Set OpenAI API key from Streamlit secrets
agent = create_agent()

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4-0613"


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
        response = agent.chat(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.experimental_rerun()
