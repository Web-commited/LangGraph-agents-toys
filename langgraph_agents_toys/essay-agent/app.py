# streamlit_app.py
import streamlit as st
from EssayAgent import EssayAgent

@st.cache_resource
def load_agent():
    return EssayAgent()

def main():
    st.title("Essay Generator Chatbot")
    
    # Load the agent
    agent = load_agent()
    
    # Slider for maximum revisions
    max_revisions = st.slider("Maximum revisions", 1, 5, 2, key="max_revisions")
    
    # Chat input for essay topic
    if prompt := st.chat_input("Enter your essay topic:"):
        # Display user's message
        with st.chat_message("user"):
            st.write(prompt)
        with st.spinner("Generating essay..."):
            agent.generate_essay(prompt, max_revisions)

if __name__ == "__main__":
    main()