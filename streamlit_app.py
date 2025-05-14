import streamlit as st
import pandas as pd
from sympy import *
from sympy.parsing.latex import parse_latex


st.write("## Errechnete Größe")
df = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\txt{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_df = st.data_editor(df, hide_index=True)

formula = st.text_input("Formel um Größe zu errechnen:", placeholder=r"\frac{m_\txt{Wasser}}{V_\txt{Wasser}")

st.write("## Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\txt{Wasser}", "Einheit": "g", "Messwert": 100, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\txt{Wasser}", "Einheit": "ml", "Messwert": 100, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")

var_names = df["Formelzeichen"].tolist()
var_units = df["Einheit"].tolist()
var_values = df["Messwert"].tolist()
var_uncert = df["Fehler"].tolist()
var_const = df["Ist Konstant"].tolist()

st.write(var_names)
st.write(var_const)
