import os
from dotenv import load_dotenv
import streamlit as st
import googlemaps
import google.generativeai as genai
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Route Summarizer",
    page_icon="🗺️",
    layout="wide"
)

# --- App Title and Description ---
st.title("🗺️ Route Summarizer AI Agent")
st.markdown("Get a simple, narrative summary of your driving route. This app uses the Google Maps API for directions and the Gemini API for a human-friendly summary.")


# Use st.secrets for deployment, with a fallback to sidebar input for local use
load_dotenv()
Maps_api = os.getenv("GOOGLE_MAPS_API")
gemini_api = os.getenv("GEMINI_API_KEY")
password = os.getenv("password")

# --- Main Interface ---
col1, col2, col3 = st.columns(3)
with col1:
    password_input = st.text_input("Password")
with col2:
    origin = st.text_input("📍 Origin")
with col3:
    dest = st.text_input("🏁 Destination")

if st.button("Generate Route Summary", type="primary", use_container_width=True):
    if password_input != password:
        st.error("Please enter correct Password")
    elif not origin or not dest:
        st.warning("⚠️ Please enter both an origin and a destination.")
    else:
        try:
            with st.spinner("Fetching directions from Google Maps... 🚗"):
                gmaps = googlemaps.Client(key=Maps_api)
                directions_result = gmaps.directions(origin, dest, mode="driving")

            if directions_result:
                # 1. Prepare the Data for Gemini
                leg = directions_result[0]['legs'][0]
                total_distance = leg['distance']['text']
                total_duration = leg['duration']['text']

                steps_list = [step['html_instructions'] for step in leg['steps']]
                all_steps_text = " ".join([re.sub('<[^<]+?>', ' ', s) for s in steps_list])

                # 2. Generate the Summary with Gemini
                with st.spinner("🤖 Asking Gemini to summarize the route..."):
                    genai.configure(api_key=gemini_api)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')

                    prompt = f"""
                    You are a helpful and friendly travel assistant.
                    Summarize the following driving directions into a short, easy-to-read narrative paragraph.
                    Start with a clear opening sentence that includes the total distance and estimated travel time.
                    Focus on major highways, key turns, and significant landmarks. Avoid mentioning every single minor turn or street name.
                    The tone should be conversational and clear, like giving advice to a friend.

                    - **Origin:** {origin}
                    - **Destination:** {dest}
                    - **Total Distance:** {total_distance}
                    - **Total Duration:** {total_duration}
                    - **Raw Steps:** "{all_steps_text}"
                    """
                    response = model.generate_content(prompt)

                # 3. Display the results
                st.subheader("✨ Your Travel Summary", anchor=False)
                st.markdown(response.text)

                with st.expander("Show Detailed Step-by-Step Directions"):
                    st.markdown(f"**Total Distance:** {total_distance}")
                    st.markdown(f"**Total Duration:** {total_duration}")
                    st.markdown("---")
                    for i, step in enumerate(steps_list):
                        clean_step = re.sub('<[^<]+?>', '', step).strip()
                        st.markdown(f"**{i+1}.** {clean_step}")

            else:
                st.error("No directions found. Please check your locations and try again.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

