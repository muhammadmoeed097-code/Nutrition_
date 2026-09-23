import streamlit as st
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# API KEY RETRIEVAL (Safe for Local & Streamlit Cloud)
# =========================================================
HARDCODED_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

cloud_secret_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        cloud_secret_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

ENV_GEMINI_API_KEY = cloud_secret_key or os.getenv("GEMINI_API_KEY", HARDCODED_API_KEY)

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Global Nutrition & AI Diet Assistant",
    page_icon="🥗",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e7e34, #28a745);
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🥗 Global Nutrition & Health AI Assistant</h1>
    <p>Powered by Google Gemini — Multi-Language Recipes, Custom Calorie Goals, Medical Filters & Hacks!</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Settings, Languages & Personal Profile Calculator
# ---------------------------------------------------------
with st.sidebar:
    st.header("🔑 API Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key", 
        value="" if ENV_GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE" else ENV_GEMINI_API_KEY, 
        type="password",
        help="Get your free key from aistudio.google.com"
    )

    final_api_key = api_key_input if api_key_input else HARDCODED_API_KEY

    # 🌐 Language Selection Option
    st.divider()
    st.header("🌐 Response Language")
    selected_language = st.selectbox(
        "Select Output Language / Zuban Chunein:",
        [
            "English", 
            "Urdu (اردو)", 
            "Hindi (हिंदी)", 
            "Roman Urdu / Hindi", 
            "Japanese (日本語)", 
            "Chinese (中文)"
        ],
        index=3  # Default set to Roman Urdu/Hindi
    )

    st.divider()
    st.header("👤 Physical Profile & Calorie Mode")
    
    # 🎯 Choice to Auto Calculate or Manually Choose Calories
    calorie_mode = st.radio(
        "Calories Select Karne Ka Tareeqah:",
        ["Auto-Calculate (Age, Weight, Height)", "Manual Custom Calories (Apni Marzi Se)"]
    )

    if calorie_mode == "Auto-Calculate (Age, Weight, Height)":
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=10, max_value=100, value=25)
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
        with col2:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0)
            gender = st.selectbox("Gender", ["Male", "Female"])

        goal = st.selectbox("Your Goal", ["Maintain Weight", "Weight Loss", "Muscle Gain", "Height Increase / Growth"])
        activity_level = st.selectbox("Activity Level", ["Sedentary (Little/No exercise)", "Moderate (3-5 days/week)", "Active (6-7 days/week)"])

        if gender == "Male":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        multipliers = {"Sedentary (Little/No exercise)": 1.2, "Moderate (3-5 days/week)": 1.55, "Active (6-7 days/week)": 1.725}
        tdee = bmr * multipliers[activity_level]

        if goal == "Weight Loss":
            target_calories = int(tdee - 500)
        elif goal in ["Muscle Gain", "Height Increase / Growth"]:
            target_calories = int(tdee + 300)
        else:
            target_calories = int(tdee)

        protein_target = int(weight * 1.8)

    else:
        # Custom Manual Calories
        target_calories = st.number_input("Enter Daily Calorie Goal (kcal):", min_value=1000, max_value=5000, value=2000, step=50)
        goal = st.selectbox("Your Goal", ["Maintain Weight", "Weight Loss", "Muscle Gain", "Height Increase / Growth"])
        protein_target = st.number_input("Enter Daily Protein Target (grams):", min_value=40, max_value=250, value=100)
        age, weight, height, gender = "N/A", "N/A", "N/A", "N/A"

    diet_pref = st.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan", "Halal", "Keto", "Lactose Free", "Gluten Free"])

    # Health & Medical Conditions Multi-select
    st.divider()
    st.header("🩺 Health & Medical Conditions")
    health_conditions = st.multiselect(
        "Select Any Medical Conditions / Concerns:",
        [
            "Diabetes / High Sugar", 
            "High Blood Pressure (Hypertension)", 
            "High Cholesterol", 
            "Uric Acid / Gout", 
            "Fatty Liver", 
            "Acid Reflux / Acidity", 
            "PCOS / PCOD", 
            "Thyroid Issues"
        ],
        help="AI will automatically customize recipes & advice based on these conditions."
    )

    st.success(f"🎯 **Target Calories:** {target_calories} kcal")
    st.info(f"💪 **Protein Target:** {protein_target}g / day")

    # Daily Calorie Split Breakdown
    st.divider()
    st.subheader("🍱 Daily Meal Calorie Split")
    b_cal = int(target_calories * 0.25)
    l_cal = int(target_calories * 0.40)
    d_cal = int(target_calories * 0.35)
    st.write(f"🌅 **Breakfast (25%):** {b_cal} kcal")
    st.write(f"☀️ **Lunch (40%):** {l_cal} kcal")
    st.write(f"🌙 **Dinner (35%):** {d_cal} kcal")

    st.divider()
    st.header("⚙️ Model Settings")
    
    selected_model = st.selectbox(
        "Gemini Model", 
        ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-1.5-flash"], 
        index=0
    )
    temperature = st.slider("Creativity Level", 0.1, 1.0, 0.7, 0.1)

    if st.button("🗑️ Clear History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# System Prompt & Language Directives
# ---------------------------------------------------------
profile_info = f"""
USER PROFILE CONTEXT:
- Mode: {calorie_mode}
- Age: {age}, Gender: {gender}, Weight: {weight}kg, Height: {height}cm
- Primary Goal: {goal}
- Target Daily Calories: {target_calories} kcal (Breakfast: {b_cal} kcal, Lunch: {l_cal} kcal, Dinner: {d_cal} kcal)
- Target Protein: {protein_target}g/day
- Dietary Restrictions: {', '.join(diet_pref) if diet_pref else 'None'}
- Medical / Health Conditions: {', '.join(health_conditions) if health_conditions else 'None / Healthy'}
"""

SYSTEM_PROMPT = f"""You are a friendly, certified nutritionist and master chef.
{profile_info}

CRITICAL RULES:
1. **Greetings & Casual Chat:** If the user says "Hi", "Hello", "Assalam-o-Alaikum", or starts casually, respond warmly in {selected_language}. Greet them, acknowledge their target ({target_calories} kcal/day), and ask how you can help.
2. **Language:** ALWAYS respond in the following user-selected language: **{selected_language}**.
3. **Medical & Custom Diet:** Adjust macros and ingredients strictly according to their health conditions and calorie goal ({target_calories} kcal).
"""

if not final_api_key or final_api_key == "YOUR_GEMINI_API_KEY_HERE":
    st.warning("⚠️ Please enter your Google Gemini API Key in the sidebar or setup GEMINI_API_KEY in secrets!")
    st.stop()

# Initialize GenAI Client
client = genai.Client(api_key=final_api_key)

# ---------------------------------------------------------
# Feature 1: Dish Category & Cuisine Filters
# ---------------------------------------------------------
st.write("### 🍖 Dish Category & Cuisine Filter")

f_col1, f_col2, f_col3 = st.columns([2, 2, 1])

with f_col1:
    selected_ingredient = st.selectbox(
        "Main Ingredient / Base:",
        ["Chicken", "Beef", "Mutton", "Fish / Seafood", "Egg", "Paneer", "Daal / Legumes", "Chickpeas", "Rice Dish", "Pasta Dish", "Instant Noodles (Knorr/Shoop)", "Fruit Chaat / Salads"]
    )

with f_col2:
    selected_cuisine = st.selectbox(
        "Select Cuisine / Country Style:",
        ["Pakistani", "Indian", "South Indian", "Continental", "Asian", "Italian", "Mexican", "Japanese", "Chinese", "Any Style"]
    )

with f_col3:
    st.write(" ")
    st.write(" ")
    filter_recipe_btn = st.button("🍳 Get Recipe Idea", type="primary")

# ---------------------------------------------------------
# Feature 2: Interactive Cooking Timer
# ---------------------------------------------------------
with st.expander("⏱️ **Interactive Cooking & Prep Timer** — Food pakate waqt time monitor karein!", expanded=False):
    t_col1, t_col2, t_col3 = st.columns([2, 2, 1])
    with t_col1:
        timer_minutes = st.number_input("Minutes", min_value=0, max_value=120, value=5)
    with t_col2:
        timer_seconds = st.number_input("Seconds", min_value=0, max_value=59, value=0)
    with t_col3:
        st.write(" ")
        st.write(" ")
        start_timer = st.button("▶️ Start Timer")

    if start_timer:
        total_sec = (timer_minutes * 60) + timer_seconds
        if total_sec > 0:
            timer_placeholder = st.empty()
            for secs in range(total_sec, -1, -1):
                mins, s = divmod(secs, 60)
                timer_placeholder.markdown(f"### ⏳ Remaining Time: **{mins:02d}:{s:02d}**")
                time.sleep(1)
            timer_placeholder.success("🎉 **Time's up! Aapka khana tayyar hai!**")
            st.balloons()
        else:
            st.warning("Please set time greater than 0.")

# ---------------------------------------------------------
# Feature 3: Pantry Matcher & Quick Shortcuts
# ---------------------------------------------------------
with st.expander("🥦 **Pantry Matcher** — Ghar ke ingredients se recipe banayein!", expanded=False):
    pantry_items = st.text_input("Ghar/Kitchen mein kya kya saman pada hai? (e.g. Milk, Eggs, Oats, Nuts):")
    pantry_submitted = st.button("🍳 Find Pantry Recipe", type="secondary")

st.write("### 💡 Quick Diet Shortcuts")
col1, col2, col3, col4 = st.columns(4)

triggered_prompt = None

if col1.button("📏 Height Increase Diet"):
    triggered_prompt = f"Give me a complete daily diet plan and nutrition tips specifically for height increase/growth, focusing on Calcium, Vitamin D, Protein, and Zinc for {target_calories} kcal target. Respond in {selected_language}."
elif col2.button("💪 High Protein Lunch"):
    triggered_prompt = f"Give me a high-protein lunch recipe option aimed at achieving my protein target of {protein_target}g considering my health conditions. Respond in {selected_language}."
elif col3.button("🍜 Healthy Instant Noodles"):
    triggered_prompt = f"How can I make Knorr or Instant Noodles healthy, low sodium, and suitable for my target goal ({goal}) and medical conditions? Respond in {selected_language}."
elif col4.button("🍎 Fruit Chaat Guide"):
    triggered_prompt = f"Give me a healthy Fruit Chaat recipe and guide on how to prepare it if I only have 2 or 3 fruits at home. Respond in {selected_language}."

if filter_recipe_btn:
    triggered_prompt = f"Give me a delicious and healthy recipe featuring **{selected_ingredient}** in **{selected_cuisine}** style according to my daily calorie goal ({target_calories} kcal) and health conditions. Respond in {selected_language}."

if pantry_submitted and pantry_items.strip():
    triggered_prompt = f"I have these ingredients in my pantry: {pantry_items}. Suggest a delicious and healthy recipe I can make with them according to my diet goal ({target_calories} kcal target)! Respond in {selected_language}."

# ---------------------------------------------------------
# Chat History & Response Stream (Starting Hi/Hello)
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Assalam-o-Alaikum! 👋 Hi there! I am your AI Nutritionist & Master Chef.\n\nYour target is set to **{target_calories} kcal/day** ({protein_target}g protein).\n\nAap sidebar se calories khud choose kar sakte hain ya auto-calculate karva sakte hain. How can I help you today?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_input_text = st.chat_input("Ask anything... e.g. Hi, Hello, or recipe question!")

prompt = chat_input_text if chat_input_text else triggered_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.models.generate_content_stream(
                model=selected_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=temperature
                )
            )

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error communicating with Gemini API: {str(e)}")