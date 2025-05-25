import re as regex
import pandas as pd
import streamlit as st
from sympy import *
from sympy.parsing.latex import parse_latex
from lark.exceptions import UnexpectedEOF, UnexpectedCharacters

st.set_page_config(page_title="JCFG",)

st.title("Fehlerfortpflanzung nach Gauß")
st.text("V beta 1.0.3 Fehlerrechner von LaTex, nach LaTex.")
st.text("DISCLAIMER: Bullshit In, Bullshit Out. Überprüfe deine Rechnungen!")

# Global Settings
pd.set_option('display.float_format', lambda x: f'{x:.8f}')

# Result Input
st.subheader("Errechnete Größe")
dfRes = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\text{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_dfRes = st.data_editor(dfRes, hide_index=True)

# Formula Input
st.subheader("Formel")
formula = st.text_input("Formel um Größe zu Errechnen:", r"\frac{m_\text{Wasser}}{V_\text{Wasser}}")
st.latex(formula)

# Table for Var Input
st.subheader("Variablen")
df = pd.DataFrame(
    [
        {"Formelzeichen": r"m_\text{Wasser}", "Einheit": "g", "Messwert": 100.0, "Fehler": 0.1, "Ist Konstant": False},
        {"Formelzeichen": r"V_\text{Wasser}", "Einheit": "ml", "Messwert": 100.0, "Fehler": 0.01, "Ist Konstant": False},
   ]
)
edited_df = st.data_editor(df, num_rows="dynamic")



# Retrieve the User Input
res_name = str(edited_dfRes.iat[0, 0])
res_unit = str(edited_dfRes.iat[0, 1])
var_names = edited_df["Formelzeichen"].tolist()
var_units = edited_df["Einheit"].tolist()
var_values = edited_df["Messwert"].tolist()
var_uncert = edited_df["Fehler"].tolist()
var_const = edited_df["Ist Konstant"].tolist()

for uncertInd, uncert in enumerate(var_uncert):
	var_uncert[uncertInd] = round(uncert, int(str(var_uncert[1])[-2:])) if uncert<=0.0001 else uncert

# Replacing old names for processing
# Every Name gets a name Addon nAdd + {a,b,c,...}, defined hereafter to identify it more easily and to enable complicated Variable names without messing with Lark Translator
# Most of the Error handling happens here
nAdd = "tacit"
hasError = False
for nameInd, name in enumerate(var_names):
	var_names[nameInd] = "" if name == None else name
blackList = var_names.copy()
blackList = blackList + [nAdd ,r"\cdot", r"\frac", r"\mathit"]
for nameInd, name in enumerate(var_names):
	# Handling Major Errors
	if name == None or name == "" or name == " ":
		name = ""
		st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle ist unbenannt!", icon="🚨")
		hasError = True
	elif len(name) <= 1:
		st.error("Der Name der " + str(nameInd+1) + ". Variable in der Tabelle ist zu kurz! \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}'", icon="🚨")
		hasError = True
	elif any(	(name in bLname) and (nameInd != bLindex)
		for bLindex, bLname in enumerate(blackList)):
		st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle ist als Zeichenfolge nicht eindeutig genug, da sie im Namen anderer Variablen oder Steuerwörtern aus Latex (z.B. '\\frac') oder diesem Rechner vorkommt. \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}'", icon="🚨")
		hasError = True
	elif name not in formula:
		st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle kommt in der Formel nicht vor!", icon="🚨")
		hasError = True
	else:
		# Replacing the Variable with nAdd for processing
		formula = formula.replace(name, r"{\mathit{" + nAdd + chr(nameInd+97) + "}}")

# Other Replacements (TODO if list grows, make into Loop)
formula = formula.replace(r"\left(", "(").replace(r"\right)", ")")

# Other minor Errors
if var_const.count(True) == len(var_names):
	st.warning("Alle Variablen wurden als Konstant gelistet!", icon="⚠️")


# Process Names are put in a dictionary
symbol_dict = {nAdd+chr(nameChr+97): symbols(nAdd+chr(nameChr+97)) for nameChr in range(0,len(var_names))}

if not hasError:
	# Parse from Latex to sympy using the dictionary
	hasError = True
	try:
		form = parse_latex(formula, backend="lark")
		hasError = False
	except UnexpectedEOF:
		st.error("Eine Klammer wurde geöffnet, aber nicht geschlossen", icon="🚨")
	except UnexpectedCharacters as e:
			st.error("Die Formel enthält Abschnitte die: \n\n - Rein Formativ \n\n - Falsch geschrieben \n\n - Teil von Variablennamen sind. \n\n Bitte korrigieren Sie den Fehler oder geben sie die Variablen vollständig an. \n\n Der Fehler liegt in der Nähe von: '" + str(e).split("\n")[2][int(len(str(e).split("\n")[3])-1):] + "'", icon="🚨")
	except:
		st.error("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält", icon="🚨")





# Mode Selector
st.subheader("Modi")
modeS = st.toggle("Ableitungen nach allen Variablen")
modeR = st.toggle("Formel in Rohform")
modeD = st.toggle("Formel mit Ableitungen")
modeV = st.toggle("Formel mit Fehlerwerten")
modeC = st.toggle("Errechneter Fehler")

if hasError:
	st.error("Korrigierne sie zuerst die Fehler in der Formel und der Tabelle", icon="🚨")

if modeS and not hasError:
	### Print the PoU Formula with Derivatives
	st.subheader("Einzelableitungen")
	PoU_SingleDeriv = ""
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_SingleDeriv = latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+97)])))
		
		# Reintroduce the Original Var Names
		for nameChr, orgName in enumerate(var_names):
			PoU_SingleDeriv = PoU_SingleDeriv.replace(nAdd+chr(nameChr+97), orgName)
		PoU_SingleDeriv = r"\begin{equation}\frac{\partial " + res_name + r"}{\partial " + name + "} = " + PoU_SingleDeriv + r"\end{equation}" # Modify for document
		st.latex(PoU_SingleDeriv)
		st.code(PoU_SingleDeriv, language="latex")
if modeR  and not hasError:
	### Calculating the Propagation of Uncertainty PoU ###
	### Print the Raw PoU Formula
	st.subheader("Rohformel")
	PoU_Raw = r"\begin{equation} \Delta " + res_name + r" = \pm\sqrt{ \begin{split} &"
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]: # Dont't derive for constants
			continue
		PoU_Raw += r"\left(\frac{\partial " + res_name + r"}{\partial " + name + r"}\Delta " + name + r"\right)^{2} \\ &+ "
	PoU_Raw = PoU_Raw[:-3] + r"\end{split}}\end{equation}"		# Cut the last three chars ( + ) and add the }
	st.latex(PoU_Raw)
	st.code(PoU_Raw, language="latex")

if (modeD or modeV or modeC) and not hasError: # Required for V, C
	### Print the PoU Formula with Derivatives
	PoU_Diff = r"\pm\sqrt{ \begin{split} &"
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_Diff += r"\left(" + str(latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+97)])))) + r"\Delta " + nAdd+chr(nameChr+97) + r"\right)^{2} \\ &+ "
	PoU_Diff = PoU_Diff[:-7] + "\end{split} }"
	# Create Copies fo different uses
	PoU_Val = PoU_Diff
	PoU_Calc = PoU_Diff
	
	# Reintroduce the Original Var Names
	for nameChr, name in enumerate(var_names):
		PoU_Diff = PoU_Diff.replace(nAdd+chr(nameChr+97), name)
	PoU_Diff = r"\begin{equation} \Delta " + res_name + " = " + PoU_Diff + r"\end{equation}" # Modify for document
	if modeD:
		st.subheader("Formel mit Ableitungen")
		st.latex(PoU_Diff)
		st.code(PoU_Diff, language="latex")


if modeV and not hasError:
	### Print the PoU Formula with Values
	# Replace var names with their values and units, same for the uncertainties (preceeded by \Delta)
	st.subheader("Formel mit Fehlerwerten")
	for nameChr, name in enumerate(var_names):
		# If Uncertainties are too small and are shown in scientific format, format them into decimal
		if var_uncert[nameChr] < 0.0001:
			precision = str(var_uncert[nameChr])[-2:]
			PoU_Val = PoU_Val.replace(r"\Delta " + nAdd+chr(nameChr+97), "\cdot" + f"{var_uncert[nameChr]:.{precision}f}" + " \mathrm{" + str(var_units[nameChr]) + "}")
		else:
			PoU_Val = PoU_Val.replace(r"\Delta " + nAdd+chr(nameChr+97), "\cdot" + str(var_uncert[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
		PoU_Val = PoU_Val.replace(nAdd+chr(nameChr+97), str(var_values[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
	PoU_Val = r"\begin{equation} \Delta "  + res_name + " = " + PoU_Val + r"\end{equation}" # Modify for document
	
	# Finding unwanted spaces between a value und a number from the formula
	PoU_Val = re.sub(r"(?<=\d)\s+(?=\d)", r"\cdot", PoU_Val)
	
	st.latex(PoU_Val)
	st.code(PoU_Val, language="latex")
	if "nan" in PoU_Val:
		st.warning("Nan in der Formel gefunden! Überprüfen sie ob Messwerte fehlen.", icon="⚠️")


if modeC and not hasError:
	### Calculate the Uncertainty
	st.subheader("Errechneter Fehler")
	PoU_Calc = PoU_Calc[3:]
	for nameChr, name in enumerate(var_names):
		# If Uncertainties are too small and are shown in scientific format, format them into decimal
		if var_uncert[nameChr] < 0.0001:
			precision = str(var_uncert[nameChr])[-2:]
			PoU_Calc = PoU_Calc.replace(r"\Delta " + nAdd+chr(nameChr+97), " * " + f"{var_uncert[nameChr]:.{precision}f}")
		else:
			PoU_Calc = PoU_Calc.replace(r"\Delta " + nAdd+chr(nameChr+97), " * " + str(var_uncert[nameChr]))
		PoU_Calc = PoU_Calc.replace(nAdd+chr(nameChr+97), str(var_values[nameChr]))
		PoU_Calc = PoU_Calc.replace(r"\begin{split} &", "").replace(r"\end{split}", "").replace(r"\\ &", "")
	
	try:
		PoU_CalcOut = str(parse_latex(PoU_Calc, backend="lark"))
		
		st.latex(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}")
		st.code(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}", language="latex")
		
		if PoU_CalcOut == "nan":
			st.error("Division durch Null", icon="🚨")

	except:
		st.error("Kann es sein das Werte in der Tabelle fehlen? Wenn nicht prüfe die Variablen und Formeln", icon="🚨")
