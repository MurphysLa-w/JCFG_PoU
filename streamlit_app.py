import pandas as pd
import streamlit as st

if "scores" not in st.session_state:
    st.session_state.scores = [
        {"name": "Josh", "Pushups": 10, "Situps": 20},
    ]


def new_scores():
    st.session_state.scores.append(
        {
            "name": st.session_state.name,
            "Pushups": st.session_state.pushups,
            "Situps": st.session_state.situps,
        }
    )


st.write("# Score table")

score_df = pd.DataFrame(st.session_state.scores)
score_df["total_points"] = score_df["Pushups"] + score_df["Situps"]

st.write(score_df)

st.write("# Add a new score")
with st.form("new_score", clear_on_submit=True):
    name = st.text_input("Name", key="name")
    pushups = st.number_input("Pushups", key="pushups", step=1, value=0, min_value=0)
    situps = st.number_input("Situps", key="situps", step=1, value=0, min_value=0)
    st.form_submit_button("Submit", on_click=new_scores)

if(st.button("Delete")):
    del st.session_state[1]
