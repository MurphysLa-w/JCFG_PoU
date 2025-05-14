import streamlit as st
import pandas as pd
from sympy import *
from sympy.parsing.latex import parse_latex


st.subheader("Errechnete Größe")
dfRes = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\text{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_dfRes = st.data_editor(dfRes, hide_index=True)

st.subheader("Formel")
formula = st.text_input("Formel um Größe zu errechnen:", r"\frac{m_\text{Wasser}}{V_\text{Wasser}}")

st.subheader("Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\text{Wasser}", "Einheit": "g", "Messwert": 100, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\text{Wasser}", "Einheit": "ml", "Messwert": 100, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")


st.subheader("Modi")
modeS = st.toggle("Ableitungen nach allen Variablen")
modeR = st.toggle("Formel in Rohform")
modeD = st.toggle("Formel mit Ableitungen")
modeV = st.toggle("Formel mit Fehlerwerten")
modeC = st.toggle("Errechneter Wert")

res_name = str(edited_dfRes.iat[0, 0])
res_unit = str(edited_dfRes.iat[0, 1])
var_names = edited_df["Formelzeichen"].tolist()
var_units = edited_df["Einheit"].tolist()
var_values = edited_df["Messwert"].tolist()
var_uncert = edited_df["Fehler"].tolist()
var_const = edited_df["Ist Konstant"].tolist()

# Replacing old names for processing
# Every Name gets a name Addon, defied hereafter to identify it more easily
nAdd = 'jj'
for nameChr, name in enumerate(var_names):
	formula = formula.replace(name, r"{\mathit{" + nAdd + chr(nameChr+106) + "}}")

# Process Names are put in a dictionary
symbol_dict = {nAdd+chr(nameChr+106): symbols(nAdd+chr(nameChr+106)) for nameChr in range(0,len(var_names))}

# Parse from Latex to sympy using the dictionary
form = parse_latex(formula, backend="lark")

if modeS:
	### Print the PoU Formula with Derivatives
	PoU_SingleDeriv = ""
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_SingleDeriv = latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+106)])))
		
		# Reintroduce the Original Var Names
		for nameChr, orgName in enumerate(var_names):
			PoU_SingleDeriv = PoU_SingleDeriv.replace(nAdd+chr(nameChr+106), orgName)
		PoU_SingleDeriv = r"\begin{equation}\frac{\partial " + res_name + r"}{\partial " + name + "} = " + PoU_SingleDeriv + r"\end{equation}" # Modify for document
		#st.write(PoU_SingleDeriv)
		st.latex(PoU_SingleDeriv)
		st.markdown(PoU_SingleDeriv)
