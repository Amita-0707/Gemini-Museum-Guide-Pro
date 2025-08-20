# main.py
import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# For voice recognition
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder

# Load environment variables from .env file (for local testing)
load_dotenv()

# The API key is now loaded securely from Streamlit secrets
try:
    gemini_api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    st.error("API key not found. Please set 'GOOGLE_API_KEY' in your Streamlit secrets.")
    st.stop()

# Model setup
MODEL_NAME = "gemini-1.5-flash-latest"
vision_model = genai.GenerativeModel(MODEL_NAME)
chat_model = genai.GenerativeModel(MODEL_NAME)
chat = chat_model.start_chat(history=[])

# Streamlit config
st.set_page_config(page_title="Gemini Museum Guide Pro", layout="wide")
st.title("🏛️ Gemini Museum Guide Pro")
st.caption("Step into the past with AI as your museum guide.")

# Session state for history and fun facts
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "fun_facts_history" not in st.session_state:
    st.session_state["fun_facts_history"] = []

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🖼️ Artifact Explorer", "💬 Smart Tour Chatbot", "🗣️ Voice Guide", "🎲 Cultural Fun Fact", "🗂️ Tour Log"])

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

---
# --- Tab 3: Voice Guide ---
with tab3:
    st.header("🗣️ Talk to the Guide")
    st.markdown("Click the mic and speak your question.")
    
    # Use the mic_recorder component to record audio
    audio_bytes = mic_recorder(start_prompt="🎙️ Start Speaking", stop_prompt="⏹️ Stop Recording")

    if audio_bytes:
        recognizer = sr.Recognizer()
        
        # Save the audio bytes to a temporary file
        with open("audio.wav", "wb") as f:
            f.write(audio_bytes)

        with st.spinner("Recognizing your speech..."):
            try:
                with sr.AudioFile("audio.wav") as source:
                    audio_data = recognizer.record(source)
                    voice_query = recognizer.recognize_google(audio_data)
                    st.markdown(f"**You said:** *{voice_query}*")

                    with st.spinner("Thinking..."):
                        response = chat.send_message(voice_query, stream=True)
                        full_reply = ""
                        for chunk in response:
                            st.write(chunk.text)
                            full_reply += chunk.text + " "
                        st.session_state["chat_history"].append(("You (Voice)", voice_query))
                        st.session_state["chat_history"].append(("Guide", full_reply))

            except sr.UnknownValueError:
                st.error("Could not understand audio. Please try speaking more clearly.")
            except sr.RequestError as e:
                st.error(f"Speech recognition service error: {e}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

---
# --- Tab 4: Cultural Fun Fact ---
with tab4:
    st.header("🎲 Fun Fact Generator")
    if st.button("Generate Fun Fact"):
        with st.spinner("Generating fact..."):
            fact_generated = False
            attempts = 0
            max_attempts = 5

            while not fact_generated and attempts < max_attempts:
                try:
                    prompt = "Give me a fascinating, short historical or cultural fact suitable for a museum visitor that I haven't heard before."
                    fact_response = chat_model.generate_content(prompt)
                    new_fact = fact_response.text

                    if new_fact not in st.session_state["fun_facts_history"]:
                        st.session_state["fun_facts_history"].append(new_fact)
                        st.success("🧠 Did You Know?")
                        st.write(new_fact)
                        st.session_state["chat_history"].append(("Fun Fact", new_fact))
                        fact_generated = True
                    else:
                        attempts += 1
                except ResourceExhausted:
                    st.error("Quota exceeded. Please wait a moment and try again.")
                    break
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    break

---
# --- Tab 5: Tour Log ---
with tab5:
    st.header("🗂️ Museum Tour Log")
    if not st.session_state["chat_history"]:
        st.info("No conversation history yet.")
    else:
        for role, text in st.session_state["chat_history"]:
            st.markdown(f"**{role}:** {text}")
