import pandas as pd
import re as regex
import streamlit as st
from sympy import *
from sympy.parsing.latex import parse_latex
from lark.exceptions import UnexpectedEOF, UnexpectedCharacters

# Page Header
st.set_page_config(page_title="JCFG",)
st.title("Fehlerfortpflanzung nach Gauß")
st.text("V beta 1.1.0 Fehlerrechner von LaTex, nach LaTex.")
st.text("DISCLAIMER: Bullshit In, Bullshit Out. Überprüfe deine Rechnungen!")

### Getting the User Input

# Result Input
st.subheader("Errechnete Größe")
dfRes = pd.DataFrame(
    [
       {"Formelzeichen": r"\rho_\text{Wasser}", "Einheit": "g \cdot ml^{-1}"},
   ]
)
edited_dfRes = st.data_editor(dfRes, hide_index=True)

# DEBUG Mode
DEBUG = str(edited_dfRes.iat[0, 1]) == "debug"
if DEBUG: st.info("DEBUG: Aktiv")

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


### Refine the User Input
# Most of the Error handling happens here
hasError = False

# Replacing old names for processing
nAdd = "roc"			# Used as a placeholder + {a,b,c,...} to allow use of complicated variable names without interrupting the Lark Translator



# Check for None Type Names
for nameInd, name in enumerate(var_names):
	if name == None or name in ["", " ", "  "]:
		var_names[nameInd] = ""
		name = ""
		st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle ist unbenannt!", icon="🚨")
		hasError = True

# Error about too many Vars
if len(var_names) > 26:
	st.error("Es wurden mehr als 26 Variablen angegeben!", icon="🚨")
	hasError = True

# Setting up the Blacklist
blackList = var_names.copy()
blackList = blackList + [r"\cdot", r"\frac", r"\mathit"]
for nameInd, name in enumerate(var_names):
	blackList = blackList + [nAdd+chr(nameInd+97)]

if DEBUG: st.info(formula)

# Refining the Names, check for length, ambiguity
if not hasError:
	for nameInd, name in enumerate(var_names):
		if len(name) == 1 and 'a' <= name <= 'z':
			st.error("Der Name der " + str(nameInd+1) + ". Variable in der Tabelle ist zu kurz! \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}' oder verwenden sie einen anderen.", icon="🚨")
			hasError = True
		elif len(name) == 1: #Non fatal error
			st.warning("Der Name der " + str(nameInd+1) + ". Variable in der Tabelle ist sehr kurz und könnte nicht eindeutig genug sein. \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}' oder verwenden sie einen anderen.", icon="⚠️")
		elif name not in formula:
			st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle kommt in der Formel nicht vor!", icon="🚨")
			hasError = True
		elif any(	(name in bLname) and (nameInd != bLindex)
					for bLindex, bLname in enumerate(blackList)):
			st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle ist als Zeichenfolge nicht eindeutig genug, da sie im Namen anderer Variablen oder Steuerwörtern aus Latex (z.B. '\\frac') vorkommt. \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}'", icon="🚨")		
			hasError = True
		else:
			# If no error occurred replace the Variable with nAdd for processing
			formula = formula.replace(name, r"\mathit{" + nAdd + chr(nameInd+97) + "}")

if DEBUG: st.info(formula)

# Other Replacements (TODO if list grows, make into Loop)
formula = formula.replace(r"\left(", "(").replace(r"\right)", ")")

# Preventing scientific format in small floats by casting into strings
for valInd, value in enumerate(var_values):
	if abs(var_values[valInd]) < 0.0001 and var_values[valInd] != 0:
		precision = str(var_values[valInd])[-2:]
		var_values[valInd] = f"({value:.{precision}f})"
	else:
		var_values[valInd] = str(value)

for uncInd, uncert in enumerate(var_uncert):
	if abs(var_uncert[uncInd]) < 0.0001 and var_uncert[uncInd] != 0:
		precision = str(var_uncert[uncInd])[-2:]
		var_uncert[uncInd] = f"({uncert:.{precision}f})"
	else:
		var_uncert[uncInd] = str(uncert)

# Warning about All Const
if var_const.count(True) == len(var_names) and len(var_names) != 0:
	st.warning("Alle Variablen wurden als Konstant gelistet!", icon="⚠️")



### Processing the Formula
# Process Names are put in a dictionary
symbol_dict = {nAdd+chr(nameChr+97): symbols(nAdd+chr(nameChr+97)) for nameChr in range(0,len(var_names))}

if not hasError:
	# Parse from Latex to sympy using the dictionary
	hasError = True
	try:
		form = parse_latex(formula, backend="lark")
		if DEBUG: st.info(form)
		
		try: # Catching the "dx-Tuple Bug"
			diff(form, symbol_dict[nAdd+chr(0+97)])
			hasError = False
		except Exception as e:
			st.error("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält \n\n Liegt der Fehler bei einem fehlerhaften '\cdot'?", icon="🚨")
			if DEBUG: st.exception(e)
		
	except UnexpectedEOF as e:
		st.error("Eine Klammer wurde geöffnet, aber nicht geschlossen", icon="🚨")
		if DEBUG: st.exception(e)
	except UnexpectedCharacters as e:
		errorStr = str(e).split("\n")[2][int(len(str(e).split("\n")[3])-1):]
		for nameChr, orgName in enumerate(var_names):
			errorStr = errorStr.replace(r"\mathit{"+nAdd+chr(nameChr+97)+"}", orgName)
		st.error("Die Formel enthält Abschnitte die: \n\n - Rein Formativ \n\n - Falsch geschrieben \n\n - Teil von Variablennamen sind. \n\n Bitte korrigieren Sie den Fehler oder geben sie die Variablen vollständig an. \n\n Der Fehler liegt in der Nähe von: '" + errorStr + "'", icon="🚨")
		if DEBUG: st.exception(e)
	except Exception as e:
		st.error("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält", icon="🚨")
		if DEBUG: st.exception(e)


### The Modus Operandi
# Mode Selector
st.subheader("Modi")
modeS = st.toggle("Ableitungen nach allen Variablen")
modeR = st.toggle("Formel in Rohform")
modeD = st.toggle("Formel mit Ableitungen")
modeV = st.toggle("Formel mit Fehlerwerten")
modeC = st.toggle("Errechneter Fehler")

if hasError: # Interrupt if error
	st.error("Korrigieren sie zuerst die Fehler in der Formel und der Tabelle", icon="🚨")

else: # This part is always run to check for errors in simplify
	if modeS: st.subheader("Einzelableitungen")
	PoU_SingleDeriv = ""
	for nameChr, name in enumerate(var_names):
		if var_const[nameChr]:
			continue
		PoU_SingleDeriv = latex(simplify(diff(form, symbol_dict[nAdd+chr(nameChr+97)])))
		
		if modeS:
			### Print the Singular Derivatives for each Variable
			# Reintroduce the Original Var Names
			for nameChr, orgName in enumerate(var_names):
				PoU_SingleDeriv = PoU_SingleDeriv.replace(nAdd+chr(nameChr+97), orgName)
			PoU_SingleDeriv = r"\begin{equation}\frac{\partial " + res_name + r"}{\partial " + name + "} = " + PoU_SingleDeriv + r"\end{equation}" # Modify for document
			
			st.latex(PoU_SingleDeriv)
			st.code(PoU_SingleDeriv, language="latex")
		
if modeR  and not hasError:
	### Calculating the Propagation of Uncertainty PoU
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
		PoU_Val = PoU_Val.replace(r"\Delta " + nAdd+chr(nameChr+97), "\cdot" + str(var_uncert[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
		PoU_Val = PoU_Val.replace(nAdd+chr(nameChr+97), str(var_values[nameChr]) + " \mathrm{" + str(var_units[nameChr]) + "}")
	PoU_Val = r"\begin{equation} \Delta "  + res_name + " = " + PoU_Val + r"\end{equation}" # Modify for document
	
	st.latex(PoU_Val)
	st.code(PoU_Val, language="latex")
	if "nan" in PoU_Val:
		st.warning("Nan in der Formel gefunden! Überprüfen sie ob Messwerte fehlen.", icon="⚠️")


if modeC and not hasError:
	### Calculate the Uncertainty
	st.subheader("Errechneter Fehler")
	PoU_Calc = PoU_Calc[3:]
	for nameChr, name in enumerate(var_names):
		PoU_Calc = PoU_Calc.replace(r"\Delta " + nAdd+chr(nameChr+97), " * (" + str(var_uncert[nameChr]) + ")" )
		PoU_Calc = PoU_Calc.replace(nAdd+chr(nameChr+97), str(var_values[nameChr]))
		PoU_Calc = PoU_Calc.replace(r"\begin{split} &", "").replace(r"\end{split}", "").replace(r"\\ &", "")
	try:
		if DEBUG: st.info(PoU_Calc)
		PoU_CalcOut = str(parse_latex(PoU_Calc, backend="lark"))
		if DEBUG: st.info(PoU_CalcOut)
		
		if PoU_CalcOut == "nan":
			st.error("Division durch Null!", icon="🚨")
		if "Tree" in PoU_CalcOut:
			st.warning("Die Formel liefert kein eindeutiges Ergebnis. \n\n Lösungen: " + PoU_CalcOut.replace("Tree('_ambig', ","")[:-1] , icon="⚠️")
		else:
			st.latex(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}")
			st.code(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}", language="latex")

	except Exception as e:
		st.error("Kann es sein das Werte in der Tabelle fehlen? Wenn nicht prüfe die Variablen und Formeln", icon="🚨")
		if DEBUG: st.exception(e)
