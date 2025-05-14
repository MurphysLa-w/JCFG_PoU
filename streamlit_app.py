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

formula = st.text_input("Formel um Größe zu errechnen:", placeholder=r"\frac{m_\txt{Wasser}}{V_\txt{Wasser}}")

st.write("## Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\txt{Wasser}", "Einheit": "g", "Messwert": 100, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\txt{Wasser}", "Einheit": "ml", "Messwert": 100, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")


st.write("## Modi")
modeS = st.toggle("Ableitungen nach allen Variablen")
modeR = st.toggle("Formel in Rohform")
modeD = st.toggle("Formel mit Ableitungen")
modeV = st.toggle("Formel mit Fehlerwerten")
modeC = st.toggle("Errechneter Wert")

var_names = df["Formelzeichen"].tolist()
var_units = df["Einheit"].tolist()
var_values = df["Messwert"].tolist()
var_uncert = df["Fehler"].tolist()
var_const = df["Ist Konstant"].tolist()

st.write(var_names)
st.write(var_const)

# Replacing old names for processing
# Every Name gets a name Addon, defied hereafter to identify it more easily
nAdd = 'jj'
for nameChr, name in enumerate(var_names):
	nameChr += 1
	formula = formula.replace(name, r"{\mathit{" + nAdd + chr(nameChr+106) + "}}")

# Process Names are put in a dictionary
symbol_dict = {nAdd+chr(nameChr+106): symbols(nAdd+chr(nameChr+106)) for nameChr in range(0,len(var_names))}

# Parse from Latex to sympy using the dictionary
st.write(formula)
st.write(symbol_dict)
form = parse_latex(formula, backend="lark")
st.write(form)

if modeS:
	### Print the PoU Formula with Derivatives
	PoU_SingleDeriv = ""
	for nameChr, name in enumerate(var_names):
		nameChr += 1
		if name in var_const:
			continue
		PoU_SingleDeriv = latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+106)])))
		
		# Reintroduce the Original Var Names
		for nameChr, orgName in enumerate(var_names):
			nameChr += 1
			PoU_SingleDeriv = PoU_SingleDeriv.replace(nAdd+chr(nameChr+106), orgName)
		PoU_SingleDeriv = r"\begin{equation}\frac{\partial " + var_names[0] + r"}{\partial " + name + "} = " + PoU_SingleDeriv + r"\end{equation}" # Modify for document
		print(PoU_SingleDeriv + "\n")
