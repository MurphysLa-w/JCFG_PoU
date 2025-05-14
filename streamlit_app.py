import streamlit as st
import pandas as pd
from sympy import *
from sympy.parsing.latex import parse_latex
from lark.exceptions import UnexpectedEOF, UnexpectedCharacters

st.set_page_config(page_title="JCFG",)

st.title("Fehlerfortpflanzung nach Gauß")
st.text("DISCLAIMER: Bullshit In, Bullshit Out")


st.subheader("Errechnete Größe")
dfRes = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\text{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_dfRes = st.data_editor(dfRes, hide_index=True)


st.subheader("Formel")
formula = st.text_input("Formel um Größe zu errechnen:", r"\frac{m_\text{Wasser}}{V_\text{Wasser}}")
st.latex(formula)


st.subheader("Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\text{Wasser}", "Einheit": "g", "Messwert": 100, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\text{Wasser}", "Einheit": "ml", "Messwert": 100, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")

res_name = str(edited_dfRes.iat[0, 0])
res_unit = str(edited_dfRes.iat[0, 1])
var_names = edited_df["Formelzeichen"].tolist()
var_units = edited_df["Einheit"].tolist()
var_values = edited_df["Messwert"].tolist()
var_uncert = edited_df["Fehler"].tolist()
var_const = edited_df["Ist Konstant"].tolist()

# Replacing old names for processing
# Every Name gets a name Addon, defined hereafter to identify it more easily
nAdd = 'ĵîĵ'
for nameChr, name in enumerate(var_names):
	if name == None or name == " ":
		name = " "
		st.error("Die " + str(nameChr+1) + ". Variable in der Tabelle ist unbenannt!", icon="🚨")
	if name not in formula:
		st.error("Die " + str(nameChr+1) + ". Variable in der Tabelle kommt in der Formel nicht vor!", icon="🚨")
	if "ĵîĵ" in name:
		st.error("Die Zeichenfolge 'ĵîĵ' ist in Variablen nicht erlaubt. Warum probierst du sowas überhaupt aus?!!", icon="🚨")
	
	else:
		formula = formula.replace(name, r"{\mathit{" + nAdd + chr(nameChr+106) + "}}")
else:
	# Process Names are put in a dictionary
	symbol_dict = {nAdd+chr(nameChr+106): symbols(nAdd+chr(nameChr+106)) for nameChr in range(0,len(var_names))}

	# Parse from Latex to sympy using the dictionary
	try:
		form = parse_latex(formula, backend="lark")
	except UnexpectedEOF:
		st.error("Eine Klammer wurde geöffnet, aber nicht geschlossen", icon="🚨")
	except UnexpectedCharacters as e:
		st.error("Die Formel enthält Abschnitte die entweder rein formativ sind, \n falsch geschrieben wurden oder nicht als Variable in der Tabelle maskiert wurden. \n Durchsuche deine Formel und entferne diese Stellen oder trage sie ein, falls sie Teil einer Variable sein sollten. {e}", icon="🚨")
	except:
	  st.error("Die Formel konnte nicht verarbeitet werden, es kann sein das sie Fehler enthält", icon="🚨")






st.subheader("Modi")
modeS = st.toggle("Ableitungen nach allen Variablen")
modeR = st.toggle("Formel in Rohform")
modeD = st.toggle("Formel mit Ableitungen")
modeV = st.toggle("Formel mit Fehlerwerten")
modeC = st.toggle("Errechneter Fehler")

if modeS:
	### Print the PoU Formula with Derivatives
	st.subheader("Einzelableitungen")
	PoU_SingleDeriv = ""
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_SingleDeriv = latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+106)])))
		
		# Reintroduce the Original Var Names
		for nameChr, orgName in enumerate(var_names):
			PoU_SingleDeriv = PoU_SingleDeriv.replace(nAdd+chr(nameChr+106), orgName)
		PoU_SingleDeriv = r"\begin{equation}\frac{\partial " + res_name + r"}{\partial " + name + "} = " + PoU_SingleDeriv + r"\end{equation}" # Modify for document
		st.latex(PoU_SingleDeriv)
		st.code(PoU_SingleDeriv, language="latex")
if modeR:
	### Calculating the Propagation of Uncertainty PoU ###
	### Print the Raw PoU Formula
	st.subheader("Rohformel")
	PoU_Raw = r"\begin{equation}" + res_name + r" = \pm\sqrt{ \begin{split} &"
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]: # Dont't derive for constants
			continue
		PoU_Raw += r"\left(\frac{\partial " + res_name + r"}{\partial " + name + r"}\Delta " + name + r"\right)^{2} \\ &+ "
	PoU_Raw = PoU_Raw[:-3] + r"\end{split}}\end{equation}"		# Cut the last three chars ( + ) and add the }
	st.latex(PoU_Raw)
	st.code(PoU_Raw, language="latex")

if modeD:
	### Print the PoU Formula with Derivatives
	st.subheader("Formel mit Ableitungen")
	PoU_Diff = r"\pm\sqrt{ \begin{split} &"
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_Diff += r"\left(" + str(latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+106)])))) + r"\Delta " + nAdd+chr(nameChr+106) + r"\right)^{2} \\ &+ "
	PoU_Diff = PoU_Diff[:-7] + "\end{split} }"
	# Create Copies fo different uses
	PoU_Val = PoU_Diff
	PoU_Calc = PoU_Diff
	
	# Reintroduce the Original Var Names
	for nameChr, name in enumerate(var_names):
		PoU_Diff = PoU_Diff.replace(nAdd+chr(nameChr+106), name)
	PoU_Diff = r"\begin{equation}" + res_name + " = " + PoU_Diff + r"\end{equation}" # Modify for document
	st.latex(PoU_Diff)
	st.code(PoU_Diff, language="latex")


if modeV:
	### Print the PoU Formula with Values
	# Replace var names with their values and units, same for the uncertainties (preceeded by \Delta)
	st.subheader("Formel mit Fehlerwerten")
	for nameChr, name in enumerate(var_names):
		PoU_Val = PoU_Val.replace(r"\Delta " + nAdd+chr(nameChr+106), "\cdot" + str(var_uncert[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
		PoU_Val = PoU_Val.replace(nAdd+chr(nameChr+106), str(var_values[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
	PoU_Val = r"\begin{equation}"  + res_name + " = " + PoU_Val + r"\end{equation}" # Modify for document
	st.latex(PoU_Val)
	st.code(PoU_Val, language="latex")

if modeC:
	### Calculating the dumb bitch
	st.subheader("Errechneter Fehler")
	PoU_Calc = PoU_Calc[3:]
	for nameChr, name in enumerate(var_names):
		PoU_Calc = PoU_Calc.replace(r"\Delta " + nAdd+chr(nameChr+106), " * " + str(var_uncert[nameChr]))
		PoU_Calc = PoU_Calc.replace(nAdd+chr(nameChr+106), str(var_values[nameChr]))
		PoU_Calc = PoU_Calc.replace(r"\begin{split} &", "").replace(r"\end{split}", "").replace(r"\\ &", "")
	
	st.latex(r"\begin{equation}" + res_name + " = \pm" + str(parse_latex(PoU_Calc, backend="lark")) + r" \end{equation}")
	st.code(r"\begin{equation}" + res_name + " = \pm" + str(parse_latex(PoU_Calc, backend="lark")) + r" \end{equation}", language="latex")
