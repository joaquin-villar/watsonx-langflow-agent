import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Flow configuration
API_KEY=os.getenv("LANGFLOW_API_KEY")
FLOW_ID = os.getenv("LANGFLOW_FLOW_ID")
FLOW_URL = f"http://localhost:7860/api/v1/run/{FLOW_ID}"
TWEAKS = {}

def run_flow(message, endpoint=FLOW_ID, output_type="chat", input_type="chat", tweaks=None):
    """Run the Langflow flow with the given message."""
    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY  # Authentication key from environment variable
    }
    
    try:
        response = requests.request("POST", FLOW_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error making API request: {e}")
    except ValueError as e:
        raise Exception(f"Error parsing response: {e}")

# Configure the page
st.set_page_config(
    page_title="Customer Support Agent",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .stMarkdown {
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #000000;  /* Set text color to black */
    }
    .stChatMessage[data-testid="stChatMessage"] {
        background-color: #f0f2f6;
        color: #000000;  /* Also ensure text is black */
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("🤖 Customer Support Agent")
st.markdown("""
    Welcome to our AI-powered customer support agent! I can help you with:
    - Order status and details
    - Product information
    - Shipping and delivery times
    - Returns and cancellations
    - General FAQs
    """)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader(
    "Upload a file (txt, pdf, csv, png, jpg, jpeg)",
    type=["txt", "pdf", "csv", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")

    if uploaded_file.type.startswith("image/"):
        # Show the image in the UI
        st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)

        if st.button("Send Image Info to Agent"):
            msg = f"📷 User uploaded an image: {uploaded_file.name}"
            st.session_state.messages.append({"role": "user", "content": msg})
            with st.chat_message("user"):
                st.markdown(msg)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    response = run_flow(msg)
                    result = response['outputs'][0]['outputs'][0]['results']['message']['text']
                    message_placeholder.markdown(result)
                except Exception as e:
                    message_placeholder.markdown(f"⚠️ Error: {str(e)}")

    else:
        # Handle text-like files
        file_content = uploaded_file.read()

        if uploaded_file.type == "text/plain":
            text = file_content.decode("utf-8")

        elif uploaded_file.type == "text/csv":
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            text = df.to_csv(index=False)

        elif uploaded_file.type == "application/pdf":
            from PyPDF2 import PdfReader
            pdf = PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        else:
            text = "[Unsupported file format]"

        st.text_area("Extracted Content", text[:1000], height=200)  # preview first 1000 chars

        if st.button("Send File Content to Agent"):
            st.session_state.messages.append({"role": "user", "content": text})
            with st.chat_message("user"):
                st.markdown(f"📄 Uploaded `{uploaded_file.name}` sent to the agent.")

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    response = run_flow(text)
                    result = response['outputs'][0]['outputs'][0]['results']['message']['text']
                    message_placeholder.markdown(result)
                except Exception as e:
                    message_placeholder.markdown(f"⚠️ Error: {str(e)}")

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant message placeholder
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Run the flow with the user's message
            response = run_flow(
                message=prompt,
                endpoint=FLOW_ID,
                output_type="chat",
                input_type="chat",
                tweaks=TWEAKS
            )

            # Extract the result from the response
            if isinstance(response, dict):
                result = response['outputs'][0]['outputs'][0]['results']['message']['text']
            else:
                result = response.get("result", "I apologize, but I couldn't process your request. Please try again.")
            
            message_placeholder.markdown(result)
                
        except Exception as e:
            message_placeholder.markdown(f"I apologize, but I encountered an error: {str(e)}")
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": message_placeholder.markdown})

# Add a sidebar with information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This customer support agent is powered by:
    - Langflow for Agentic orchestration
    - Watsonx.ai for natural language understanding
    - Astra DB for knowledge storage and retrieval
    - Streamlit for the user interface
    """)
    
    st.header("Example Questions")
    st.markdown("""
    Try asking:
    - What's the shipping status of order 1001?
    - What was ordered with 1003?
    - What date will order 1004 arrive?
    - How can I cancel order 1001?
    - What is your shipping policy?
    """)
    
    # Add a clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun() 