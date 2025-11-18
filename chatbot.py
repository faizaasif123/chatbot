import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json
import os

# ===== PUT YOUR API KEY HERE =====
API_KEY = "AIzaSyDuNIfU4ITO_R0yZP96zdeibZvFkP9aExQ"  # Replace with your actual API key
# =================================

# Page configuration
st.set_page_config(
    page_title="Braille Learning Assistant",
    page_icon="📖",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    h1, h2, h3 {
        color: white;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
    }
    </style>
""", unsafe_allow_html=True)

# File to store chat history
HISTORY_FILE = "chat_history.json"

# Load chat history from file
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# Save chat history to file
def save_history(messages):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving history: {e}")

# Initialize session state
if "messages" not in st.session_state:
    # Load previous history
    saved_messages = load_history()
    if saved_messages:
        st.session_state.messages = saved_messages
    else:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Hi! I'm your Braille learning assistant. Ask me anything about Braille - letters, numbers, words to convert, or how to learn!",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]

if "chat" not in st.session_state:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash',
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 500,  # Increased for better responses
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}\nPlease check your API key in the code!")
        st.session_state.chat = None

if "audio_input" not in st.session_state:
    st.session_state.audio_input = None

# System prompt for better responses
SYSTEM_PROMPT = """You are a friendly Braille learning assistant. Follow these rules:

1. ONLY answer Braille-related questions (letters, numbers, words, names, punctuation, history, learning tips)

2. When someone asks to convert a word/name to Braille:
   - Break it down LETTER BY LETTER
   - Show dot patterns for EACH letter clearly
   - Use this format:
     "Let me show you [WORD] in Braille:
     
     [Letter] = dots [pattern] 
     (Explanation: which dots are raised)
     
     Do this for each letter."

3. Give DETAILED but EASY explanations:
   - Don't be too short - explain properly
   - Use simple everyday words
   - Give examples when helpful
   - Make sure anyone can understand

4. When explaining dot patterns:
   - Braille cell has 6 dots:
     1 • • 4
     2 • • 5
     3 • • 6
   - Left column: 1, 2, 3 (top to bottom)
   - Right column: 4, 5, 6 (top to bottom)
   - Describe position clearly: "top-left", "middle-left", "bottom-right", etc.

5. Give complete answers (5-8 sentences) so user fully understands

6. Be encouraging and patient

7. If asked non-Braille questions, say: "I only help with Braille! Ask me about letters, words, or learning Braille."

Remember: Be detailed enough to be helpful, but keep language simple and friendly!"""

def get_braille_response(user_message, chat):
    """Get response from Gemini API"""
    try:
        # Combine system prompt with user message
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {user_message}\n\nYour detailed response:"
        
        response = chat.send_message(full_prompt)
        
        # Handle different response formats
        if response.parts:
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            if response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
        
        return "I couldn't generate a response. Please try rephrasing your question about Braille."
    
    except Exception as e:
        return f"❌ Error: {str(e)}\nPlease try again with a different question."

# Text-to-Speech function
def speak_text(text):
    """Convert text to speech"""
    try:
        # JavaScript for text-to-speech
        clean_text = text.replace('`', '').replace('"', '\\"').replace("'", "\\'")
        js_code = f"""
        <script>
            var msg = new SpeechSynthesisUtterance();
            msg.text = `{clean_text}`;
            msg.rate = 0.9;
            msg.pitch = 1;
            msg.volume = 1;
            window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(js_code, height=0)
    except Exception as e:
        st.error(f"Speech error: {e}")

# Header with columns
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("📖 Braille Learning Assistant")
    st.markdown("*AI-powered • Voice Enabled • History Saved*")

# Sidebar for history and controls
with st.sidebar:
    st.header("📜 Chat History")
    st.markdown(f"**Total Messages:** {len(st.session_state.messages)}")
    
    st.markdown("---")
    
    # Voice Input using audio recorder
    st.subheader("🎤 Voice Input")
    st.markdown("Use browser's speech recognition:")
    
    # HTML/JS for voice input
    voice_html = """
    <div style="text-align: center; padding: 20px;">
        <button onclick="startRecognition()" 
                style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 15px 30px; border: none; 
                       border-radius: 10px; font-size: 16px; cursor: pointer;
                       font-weight: bold;">
            🎤 Start Voice Input
        </button>
        <p id="status" style="color: white; margin-top: 10px;"></p>
        <p id="transcript" style="color: white; margin-top: 10px; font-style: italic;"></p>
    </div>
    <script>
        function startRecognition() {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            
            document.getElementById('status').textContent = '🎤 Listening...';
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('transcript').textContent = 'You said: ' + transcript;
                document.getElementById('status').textContent = '✅ Got it!';
                
                // Store in localStorage to pass to Streamlit
                localStorage.setItem('voiceInput', transcript);
            };
            
            recognition.onerror = function(event) {
                document.getElementById('status').textContent = '❌ Error: ' + event.error;
            };
            
            recognition.start();
        }
    </script>
    """
    
    st.components.v1.html(voice_html, height=200)
    
  
    
    st.markdown("---")
    
    
    
   
# Main chat area
st.markdown("### 🚀 Quick Questions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📝 Start", use_container_width=True):
        if st.session_state.chat:
            prompt = "How do I start learning Braille? Explain in detail."
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            response = get_braille_response(prompt, st.session_state.chat)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_history(st.session_state.messages)
            st.rerun()

with col2:
    if st.button("🔤 Alphabet", use_container_width=True):
        if st.session_state.chat:
            prompt = "Teach me the Braille alphabet with dot patterns for each letter"
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            response = get_braille_response(prompt, st.session_state.chat)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_history(st.session_state.messages)
            st.rerun()

with col3:
    if st.button("🔢 Numbers", use_container_width=True):
        if st.session_state.chat:
            prompt = "Explain how Braille numbers work with examples"
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            response = get_braille_response(prompt, st.session_state.chat)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_history(st.session_state.messages)
            st.rerun()

with col4:
    if st.button("💪 Practice", use_container_width=True):
        if st.session_state.chat:
            prompt = "Give me a detailed practice exercise"
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            response = get_braille_response(prompt, st.session_state.chat)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_history(st.session_state.messages)
            st.rerun()

st.markdown("---")

# Display chat messages with voice output
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Add timestamp
        if "timestamp" in message:
            st.caption(f"🕐 {message['timestamp']}")
        
        # Add speaker button for each message
        if st.button(f"🔊 Listen", key=f"speak_{idx}"):
            speak_text(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about Braille... (or use voice input in sidebar)"):
    if not st.session_state.chat:
        st.error("⚠️ API not initialized. Please check your API key in the code!")
    else:
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_braille_response(prompt, st.session_state.chat)
                st.markdown(response)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"🕐 {timestamp}")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": timestamp
        })
        
        # Save history after each message
        save_history(st.session_state.messages)
        
        # Auto-play response
        speak_text(response)
        
        st.rerun()

# Handle voice input if available
if st.session_state.audio_input:
    prompt = st.session_state.audio_input
    st.session_state.audio_input = None
    
    if st.session_state.chat and prompt:
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        response = get_braille_response(prompt, st.session_state.chat)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_history(st.session_state.messages)
        speak_text(response)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white; opacity: 0.7; font-size: 12px;'>
    <p>💡 Braille-only chatbot | Detailed & Easy answers | Voice Enabled | History Saved</p>
    <p>🎤 Use voice input from sidebar | 🔊 Click listen button to hear responses</p>
</div>
""", unsafe_allow_html=True)