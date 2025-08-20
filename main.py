import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# Load environment variables from .env file
load_dotenv()


os.environ["GOOGLE_API_KEY"] = "Your_Google_Api_key"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Set the environment variable to point to your service account key file
# Make sure you have downloaded and saved the JSON file as "chatbot.json"
# in the same directory as your main.py file.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "chatbot.json"

# The genai library will automatically find and use the credentials from the environment variable.
genai.configure()

# Model setup
MODEL_NAME = "gemini-1.5-flash-latest"
vision_model = genai.GenerativeModel(MODEL_NAME)
chat_model = genai.GenerativeModel(MODEL_NAME)
chat = chat_model.start_chat(history=[])

# Streamlit config
st.set_page_config(page_title="Gemini Museum Guide Pro", layout="wide")
st.title("🏛️ Gemini Museum Guide Pro")
st.caption("Step into the past with AI as your museum guide.")

# Session state for history
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Artifact Explorer", "💬 Smart Tour Chatbot", "🎲 Cultural Fun Fact", "🗂️ Tour Log"])

# --- Tab 1: Artifact Explorer ---
with tab1:
    st.header("🖼️ Upload & Explore Artifact")
    image_prompt = st.text_input("Ask a question about the artifact (optional):")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Artifact", use_container_width=True)

        if st.button("🔍 Analyze Artifact"):
            with st.spinner("Gemini is analyzing..."):
                try:
                    # Use the vision model for image analysis
                    response = vision_model.generate_content([image_prompt, image]) if image_prompt else vision_model.generate_content(image)
                    st.success("Here's what Gemini says:")
                    st.write(response.text)
                    st.session_state["chat_history"].append(("Artifact Insight", response.text))
                except ResourceExhausted:
                    st.error("Quota exceeded. Please wait a moment and try again.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# --- Tab 2: Smart Tour Chatbot ---
with tab2:
    st.header("💬 Ask the Virtual Guide")
    user_query = st.text_input("Ask a cultural/historical question:")

    if st.button("💡 Ask Guide"):
        if user_query:
            try:
                with st.spinner("Thinking..."):
                    response = chat.send_message(user_query, stream=True)
                    full_reply = ""
                    for chunk in response:
                        st.write(chunk.text)
                        full_reply += chunk.text + " "
                    st.session_state["chat_history"].append(("You", user_query))
                    st.session_state["chat_history"].append(("Guide", full_reply))
            except ResourceExhausted:
                st.error("Quota exceeded. Please wait a moment and try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Tab 3: Cultural Fun Fact ---
with tab3:
    st.header("🎲 Fun Fact Generator")
    if st.button("Generate Fun Fact"):
        try:
            with st.spinner("Generating fact..."):
                prompt = "Give me a fascinating, short historical or cultural fact suitable for a museum visitor."
                fact_response = chat_model.generate_content(prompt)
                st.success("🧠 Did You Know?")
                st.write(fact_response.text)
                st.session_state["chat_history"].append(("Fun Fact", fact_response.text))
        except ResourceExhausted:
            st.error("Quota exceeded. Please wait a moment and try again.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- Tab 4: Tour Log ---
with tab4:
    st.header("🗂️ Museum Tour Log")
    if not st.session_state["chat_history"]:
        st.info("No conversation history yet.")
    else:
        for role, text in st.session_state["chat_history"]:
            st.markdown(f"**{role}:** {text}")