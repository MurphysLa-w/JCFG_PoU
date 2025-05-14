import streamlit as st
import pandas as pd


st.text_input("Formula:", placeholder=r"\frac{m_\txt{Wasser}}{V_\txt{Wasser}")


st.write("## Errechnete Größe")
df = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\txt{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_df = st.data_editor(df)

st.write("## Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\txt{Wasser}", "Einheit": "g", "Messwert": 100, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\txt{Wasser}", "Einheit": "ml", "Messwert": 100, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")

