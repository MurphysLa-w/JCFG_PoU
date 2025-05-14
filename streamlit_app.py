import streamlit as st
import pandas as pd


st.text_input("Formula:", r"\frac{m_\txt{Wasser}}{V_\txt{Wasser}")


st.write("# Variablen")
df = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\txt{Wasser}", "Einheit": "g", "Messwert": 16.8, "Fehler": 0.01, "Ist Konstant": True},
   ]
)
edited_df = st.data_editor(df)

st.write("# Variablen")
df = pd.DataFrame(
    [
       {"Formelzeichen": r"m_\txt{Wasser}", "Einheit": "g", "Messwert": 16.8, "Fehler": 0.01, "Ist Konstant": True},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")

