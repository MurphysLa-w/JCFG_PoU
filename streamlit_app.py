import streamlit as st
import pandas as pd


st.write("# Variablen")
df = pd.DataFrame(
    [
       {"Formelzeichen": "m_\txt{Wasser}", "Einheit": "g", "Messwert": 16.8, "Fehler": 0.01, "Ist Konstant": True},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")

st.write(edited_df.iat[1, 1])
