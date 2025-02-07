# app.py
import streamlit as st
from agent import Agent  # Import your Agent class from the original file

# Set up page configuration
st.set_page_config(page_title="Claude-3 Chat Agent", page_icon="🤖")

# initialization
if "agent" not in st.session_state:
    st.session_state.agent = Agent()

# Handle user input first
if prompt := st.chat_input("Type your message here..."):

    response = st.session_state.agent(prompt)

# Display chat history
for message in st.session_state.agent.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"][0]["text"])