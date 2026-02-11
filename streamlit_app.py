import altair
import requests
import datetime
import re as regex
import pandas as pd
import streamlit as st
from sympy import *
from io import StringIO
from sympy.parsing.latex import parse_latex
from lark.exceptions import UnexpectedEOF, UnexpectedCharacters

# Used later in Refining to wrap the log expressions to kill ambiguous Trees
def wrap_log_expr(text):
	result = []
	i = 0
	while i < len(text):
		if text[i:i+5] == r"\log{":
			start = i
			i += 5
			brace_depth = 1
			while i < len(text) and brace_depth > 0:
				if text[i] == "{":
					brace_depth += 1
				elif text[i] == "}":
					brace_depth -= 1
				i += 1
			log_expr = text[start:i]
			result.append(f"({log_expr})")
		else:
			result.append(text[i])
			i += 1
	return "".join(result)


### Page Header
st.set_page_config(page_title="JCFG",)
st.title("Fehlerfortpflanzung nach Gauß")
st.text("V beta 1.4.2 Fehlerrechner von LaTex, nach LaTex.")
st.text("DISCLAIMER: Bullshit In, Bullshit Out. Überprüfen Sie ihre Rechnungen!")



### Sidebar
st.sidebar.header("Editor")
## Setting Up Editor Buttons
with st.sidebar:
	editor = st.expander("Werkzeuge")
	col1, col2, col3, col4 = editor.columns(4 ,vertical_alignment="center")
	
	undo = col1.button("",icon=":material/undo:", help="Rückgängig", use_container_width=True)
	redo = col2.button("",icon=":material/redo:", help="Wiederherstellen", use_container_width=True)
	
# Mode Selector
st.sidebar.header("Modi")
modeS = st.sidebar.toggle("Ableitungen nach allen Variablen")
modeR = st.sidebar.toggle("Formel in Rohform")
modeD = st.sidebar.toggle("Formel mit Ableitungen")
modeV = st.sidebar.toggle("Formel mit Fehlerwerten")
modeC = st.sidebar.toggle("Errechneter Fehler")

# Debug
st.sidebar.subheader("DEBUG")
DEBUG = st.sidebar.toggle("Debug-Modus")
DEVMODE = False
if DEBUG:
	st.info("DEBUG: Aktiv")
	DEVMODE = st.sidebar.toggle("Tech-Debug")

hasError = False




### Getting the User Input
## Setting Up the History and defining defaults
# History is a list with all previous states. Every state is a list containing the result table(dict), the formula(str) and the var table(list of dict) in this order
if "index" not in st.session_state:
	st.session_state.index = 0
if "history" not in st.session_state:
	st.session_state.history = [#hist
		[#state
			[{"Formelzeichen": r"\rho_\text{Wasser}", "Einheit": "g \cdot ml^{-1}"}],
			
			r"\frac{m_\text{Wasser}}{V_\text{Wasser}}",
			
			[{"Formelzeichen": r"m_\text{Wasser}", "Einheit": "g", "Messwert": 100.0, "Fehler": 0.1, "Ist Konstant": False},
			{"Formelzeichen": r"V_\text{Wasser}", "Einheit": "ml", "Messwert": 100.0, "Fehler": 0.01, "Ist Konstant": False}]
		]
	]
if "data" not in st.session_state:
	st.session_state.data = st.session_state.history[st.session_state.index]


# Undo moves Index back and shows datastate at index
if undo and st.session_state.index != 0:
	st.session_state.index += -1
	st.session_state.data = st.session_state.history[st.session_state.index]

# Undo moves Index forward and shows datastate at index
if redo and st.session_state.index != len(st.session_state.history)-1:
	st.session_state.index += 1
	st.session_state.data = st.session_state.history[st.session_state.index]


## Displaying current state
# Result Input with dict from state as base
st.subheader("Errechnete Größe")
edited_dfRes = st.data_editor(pd.DataFrame(st.session_state.data[0]), hide_index=True)
# Compress the row back to dictlist with one row
dictRes = edited_dfRes.to_dict(orient='records')
st.latex(dictRes[0]["Formelzeichen"] + "~/~\mathrm{" + dictRes[0]["Einheit"] + "}")


# Formula Input with str from state as base
st.subheader("Formel")
formula = st.text_input("Formel um Größe zu Errechnen:", st.session_state.data[1])
st.latex(formula)

# Table for Var Input with list of dict from state as base
st.subheader("Variablen")
edited_df = st.data_editor(pd.DataFrame(st.session_state.data[2]), num_rows="dynamic")
# Compress back to dictlist
dictVar = edited_df.to_dict(orient='records')


# Get the current state
current_state = [dictRes, formula, dictVar]


## Updating history if anything has been edited
if not undo and str(st.session_state.history[st.session_state.index]) != str(current_state):
	
	# Delete History that might now be "in the future" as every edit is the latest change and most recent in history
	while len(st.session_state.history) > st.session_state.index+1:
		st.session_state.history.pop()
	
	# Append this change to history and move the index to "now"
	st.session_state.history.append(current_state)
	st.session_state.index = len(st.session_state.history)-1
	
	# Update state and rerun to make sure its the new base state for the st.data_editor
	st.session_state.data = st.session_state.history[st.session_state.index]
	st.rerun()




### Export and Import
# Export via String
str_import = ""
export_inputs = col3.button("",icon=":material/output_circle:", help="Exportiere Eingaben als String", use_container_width=True, disabled=not DEVMODE)
if export_inputs:
	csv_buffer = StringIO()
	edited_dfRes.to_csv(csv_buffer, index=False)
	csv_string = csv_buffer.getvalue() + "%%%" + formula
	csv_buffer = StringIO()
	edited_df.to_csv(csv_buffer, index=False)
	csv_string = csv_string + "%%%" + csv_buffer.getvalue()
	editor.text_input("Import/Export als String", value=csv_string.replace("\n", "§§§"))
	
elif DEVMODE:
	str_import = editor.text_input("Import/Export als String", placeholder="Importiere Eingaben")


# Import via string
# Check and warn before imports
str_import_check = [match.start() for match in regex.finditer("%%%", str_import)]
import_inputs = col4.button("",icon=":material/input_circle:", help="Importiere Eingaben als String", use_container_width=True, disabled=(len(str_import_check) != 2) or not DEVMODE)
if len(str_import_check) == 2:
	editor.warning("Import only if you know what you are doing", icon="❗️")
	
# Import
if import_inputs:
	try:
		str_import = str_import.replace("§§§", "\n")
	
		# Get the three state sections and read them as csv into a DataFrame and convert to dict, then safe to history and update it
		st.session_state.history.append([pd.read_csv(StringIO(str_import.split("%%%")[0])).to_dict(orient='records'),
		str_import.split("%%%")[1],
		pd.read_csv(StringIO(str_import.split("%%%")[2])).to_dict(orient='records')])
		
		st.session_state.index = len(st.session_state.history)-1
		
		# Update state and rerun to make sure its the new base state for the st.data_editor
		st.session_state.data = st.session_state.history[st.session_state.index]
	except:
		st.error("Import fehlgeschlagen", icon="🚨")
	else:
		st.rerun()

# Show History
if DEVMODE:
	with st.expander("DEBUG Verlauf"):
		st.info("Aktueller Index:   " + str(st.session_state.index))
		st.json(st.session_state.history, expanded=1)




### Retrieve the User Input
res_name = str(dictRes[0]["Formelzeichen"])
res_unit = str(dictRes[0]["Einheit"])
var_names = edited_df["Formelzeichen"].tolist()
var_units = edited_df["Einheit"].tolist()
var_values = edited_df["Messwert"].tolist()
var_uncert = edited_df["Fehler"].tolist()
var_const = edited_df["Ist Konstant"].tolist()

with st.expander("Variablen in LaTex Form"):
	for i, var in enumerate(var_names):
		st.latex(str(var_names[i]) + "~/~\mathrm{" + str(var_units[i]) + "}=" + str(var_values[i]) + "\pm" + str(var_uncert[i]))




### Refine the User Input
# Most of the Error handling happens here

if DEBUG:
	st.info("Vor Aufbereitung:   " + str(formula))
bug_formula = formula

# Replacing old names for processing
nAdd = "roc"			# Used as a placeholder + {a,b,c,...} to allow use of complicated variable names without interrupting the Lark Translator

# Check for None Type Names
for nameInd, name in enumerate(var_names):
	if name == None or name in ["", " ", "  "]:
		var_names[nameInd] = ""
		name = ""
		st.error("Die " + str(nameInd+1) + ". Variable in der Tabelle ist unbenannt!", icon="🚨")
		hasError = True


# Warning if Misused
if "=" in formula:
	st.warning("Die Formel enthält ein '=' Zeichen. In das Formelfeld gehört ausschließlich die Formel um die Größe zu berechnen, die darüber definiert wurde", icon="⚠️")
	hasError = True

# Error about too many Vars
if len(var_names) > 26:
	st.error("Es wurden mehr als 26 Variablen angegeben!", icon="🚨")
	hasError = True

# Error for 0 Vars
if len(var_names) == 0:
	st.error("Es wurden keine Variablen angegeben!", icon="🚨")
	hasError = True

# Warning about All Const
if var_const.count(True) == len(var_names) and len(var_names) != 0:
	st.warning("Alle Variablen wurden als Konstant gelistet!", icon="🚨")
	hasError = True


# Setting up the Blacklist
blackList = var_names.copy()
blackList = blackList + [r"\cdot", r"\frac", r"\mathit", r"\log", r"\ln", r"e^"]
for nameInd, name in enumerate(var_names):
	blackList = blackList + [r"\mathit{"+nAdd+chr(nameInd+97)+"}"]

# Refining the Names, check for length, ambiguity
if not hasError:
	for nameInd, name in enumerate(var_names):
		if len(name) == 1 and 'a' <= name <= 'z':
			st.error("Der Name der " + str(nameInd+1) + ". Variable in der Tabelle ist zu kurz! \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}' oder verwenden sie einen anderen.", icon="🚨")
			hasError = True
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
		
		if len(name) == 1: #Non fatal error
			st.warning("Der Name der " + str(nameInd+1) + ". Variable in der Tabelle ist sehr kurz und könnte nicht eindeutig genug sein. \n\n Verlängern Sie z.B. den Namen 'c' zu 'c_\\text{a}' oder verwenden sie einen anderen.", icon="⚠️")


# Other Replacements
formula = formula.replace(r"\left(", "(").replace(r"\right)", ")")	#Replace \left( \right) with ()
formula = formula.replace("e^", r"\exp")							#Replace e^ with \exp to make an exponential function

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

if DEBUG: st.info("Nach Aufbereitung:   " + str(formula))



### Processing the Formula
# Process Names are put in a dictionary
symbol_dict = {nAdd+chr(nameChr+97): symbols(nAdd+chr(nameChr+97)) for nameChr in range(0,len(var_names))}

if not hasError:
	# Parse from Latex to sympy using the dictionary
	hasError = True
	try:
		form = parse_latex(formula, backend="lark")
		if DEBUG: st.info("Nach Übersetzung:   " + str(form))
		
		# Catching the "dx-Tuple Bug"
		try:
			diff(form, symbol_dict[nAdd+chr(0+97)])
			hasError = False
		except AttributeError as e:
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
	
	except SympifyError as e:
		st.error("Es ist nicht eindeutig genug, welcher Exponent/Logarythmus wo zu gehört. \n\n Setzen Sie zur Sicherheit um jede Exponentenbasis und jeden logarythmierten Term '()' KLammern um Eindeutigkeit zu schaffen. \n\n - e^{X} + Y -> (e^{X}) + Y \n\n - \ln{X} + Y -> (\ln{X}) + Y usw.", icon="🚨")
		if DEBUG: st.exception(e)
	
	except Exception as e:
		st.error("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält", icon="🚨")
		if DEBUG: st.exception(e)


### The Modus Operandi
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
			
			# Converting to German notation
			PoU_SingleDeriv = PoU_SingleDeriv.replace(".", ",")
			if "log" in PoU_SingleDeriv:
				PoU_SingleDeriv = PoU_SingleDeriv.replace("log", "ln") 
			
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
		
		# Converting to German notation
		PoU_Diff = PoU_Diff.replace(".", ",")
		if "log" in PoU_Diff:
			PoU_Diff = PoU_Diff.replace("log", "ln") 
		
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
	
	# Refining
	PoU_Val = regex.sub(r"(?<=\d) (?=\d)", r" \\cdot " , PoU_Val)	#Replace spaces between numbers with a \cdot
	
	# Converting to German notation
	PoU_Val = PoU_Val.replace(".", ",")
	if "log" in PoU_Val:
		PoU_Val = PoU_Val.replace("log", "ln") 
	
	st.latex(PoU_Val)
	st.code(PoU_Val, language="latex")
	if "nan" in PoU_Val:
		st.warning("Nan in der Formel gefunden! Überprüfen sie ob Messwerte fehlen.", icon="⚠️")


if modeC and not hasError:
	### Calculate the Uncertainty
	st.subheader("Errechneter Fehler")
	if DEBUG: st.info("Vor Aufbereitung:   " + str(PoU_Calc))
	PoU_Calc = PoU_Calc[3:]
	PoU_Calc = PoU_Calc.replace(r"\begin{split} &", "").replace(r"\end{split}", "").replace(r"\\ &", "")
	PoU_Calc = regex.sub(r"(?<!Delta)(?<!\+)(?<!-) (?=roc[a-z])", r" \\cdot " , PoU_Calc)		#Add * beteen two vars
	PoU_Calc = regex.sub(r"(roc[a-z]\^\{2\})", r"(\1)", PoU_Calc)					#Encasing squares with ()
	for nameChr, name in enumerate(var_names):
		PoU_Calc = PoU_Calc.replace(r"\Delta " + nAdd+chr(nameChr+97), " * (" + str(var_uncert[nameChr]) + ")" )
		PoU_Calc = PoU_Calc.replace(nAdd+chr(nameChr+97), "(" + str(var_values[nameChr]) + ")")
	
	# Refining
	PoU_Calc = PoU_Calc.replace(r"\left(", "(").replace(r"\right)", ")") 			#Replace ()
	PoU_Calc = PoU_Calc.replace("e^", r"\exp")										#Replace e^ with \exp to make an exponential function
	PoU_Calc = regex.sub(r"(?<=[^+\-*\/({t]) \\log", r" \\cdot \\log" , PoU_Calc)	#Add * before log if missing
	PoU_Calc = regex.sub(r"\) \(", r") \\cdot (" , PoU_Calc)						#Add * between () ()
	PoU_Calc = regex.sub(r"\^\{2\} \(", r"^\{2\} \\cdot (" , PoU_Calc)				#Add * between ^{2} (	TODO This is only for squares
	PoU_Calc = wrap_log_expr(PoU_Calc)												#Make \log{} to (\log{})
	
	
	try:
		if DEBUG: st.info("Nach 2. Aufbereitung:   " + str(PoU_Calc))
		PoU_CalcOut = str(parse_latex(PoU_Calc, backend="lark"))
		if DEBUG: st.info("Nach Berechnung:   " + str(PoU_CalcOut))
		
		if PoU_CalcOut == "nan":
			st.error("Division durch Null!", icon="🚨")
		elif "Tree" in PoU_CalcOut:
			st.warning("Die Formel liefert kein eindeutiges Ergebnis. \n\n Lösungen: " + PoU_CalcOut.replace("Tree('_ambig', ","")[:-1] , icon="⚠️")
		elif "nan" in PoU_Calc:
			st.warning("Nan in der Formel gefunden! Überprüfen sie ob Messwerte fehlen. \n\n " + PoU_Calc, icon="⚠️")
		else:
			# Converting to German notation
			PoU_CalcOut = PoU_CalcOut.replace(".", ",")
			
			st.latex(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}")
			st.code(r"\begin{equation} \Delta " + res_name + " = \pm" + PoU_CalcOut + r" \end{equation}", language="latex")

	except Exception as e:
		st.error("Formel konnte nicht ausgerechnet werden. Prüfen Sie Formel und Variablen", icon="🚨")
		if DEBUG: st.exception(e)



### Bug Reporting to a google form
# URL for the bug report form
google_form_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSeVAsZtEX3mRK8sPX_FiMO2mYMY2CVXj8nm41YOtwZyEcbuSg/formResponse"

# Dialog window for the report
@st.dialog("Feedback / Bug melden")
def bug_dialog():
	# Setting Up the Dialog
	with st.form("Bug Melden"):
		bug_kind = st.selectbox("Art:", ("Feedback", "Falsches Ergebnis", "Eingabe-/Verarbeitungsfehler", "Sonstiges"),)
		bug_desc = st.text_area("Eigene Beschreibung:")
		bug_email = st.text_input("Email Adresse für Rückmeldungen/Hilfe", placeholder=("(Optional)"))
		submit = st.form_submit_button("Absenden")
		
		# Gathering the sent data
		if submit:
			# Export the Inputs as string
			bug_csv_buffer = StringIO()
			edited_dfRes.to_csv(bug_csv_buffer, index=False)
			bug_str = bug_csv_buffer.getvalue() + "%%%" + bug_formula
			bug_csv_buffer = StringIO()
			edited_df.to_csv(bug_csv_buffer, index=False)
			bug_str = bug_str + "%%%" + bug_csv_buffer.getvalue()
			bug_str = bug_str.replace("\n", "§§§")
			
			bug_report = {
			"entry.320798035"	: bug_kind,
			"entry.1002995150"	: bug_desc,
			"entry.519864065"	: bug_email,
			"entry.74602100"	: bug_str,
			"entry.322557982"	: bug_formula,
			"entry.1381747175"	: str(var_names)[2:-2].replace("', '", "\n"),
			"entry.1326671232"	: str(var_units)[2:-2].replace("', '", "\n"),
			"entry.1324014979"	: str(var_values)[2:-2].replace("', '", "\n"),
			"entry.1897719759"	: str(var_uncert)[2:-2].replace("', '", "\n"),
			"entry.101700465"	: str(var_const)[1:-1].replace(", ", "\n"),
			}
		
			# Posting it to the form
			res = requests.post(google_form_url, data=bug_report)
			
			# Check sucess
			if res.status_code == 200 and bug_email != "":
					st.success("Erfolgreich gesendet \n\n Wir werden uns baldmöglichst zurückmelden. \n\n Die Emailadresse wird sofort nach Bearbeitung gelöscht werden.")
			elif res.status_code == 200:
				st.success("Erfolgreich gesendet")
			else:
				st.warning("Konnte nicht gesendet werden. Versuchen Sie es später erneut")
	st.caption("Das Melden Tool dient zur Entwicklung und Verbesserung dieses Rechners. Gerne können auch Anmerkungen und Kritik hierüber angebracht werden. Erfasst werden nur die derzeitigen Eingaben in den Rechner, daher kann keine direkte Rückmelung gegeben werden, wenn keine Emailadresse angegeben wird. Emailadressen werden sofort nach Bearbeitung gelöscht.  \n\n Bitte keinen Spam")

# Button to call the dialog
if st.sidebar.button("Feedback / Bug Melden", type="primary"):
	bug_dialog()
	





### Logging visit timestamps
# URL for the Log
google_log_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSd17V0q-9yM1DKa7cpxGGiRbi-NnSL2VNcdH4RPE8tcxSDh4Q/formResponse"
# Log Interval for open sessions in seconds
LOG_AFTER = 600

# Get the time
now = datetime.datetime.utcnow()

# If new Session, log immediately and set states
if "session_start" not in st.session_state and bug_formula != r"\frac{m_\text{Wasser}}{V_\text{Wasser}}":
	requests.post(google_log_url, data={"entry.644797731":"Session_Ping"})
	st.session_state.session_start = True
	st.session_state.last_logged = now
	
# If session still open and the last log was long ago a rerun triggers another log
elif "session_start" in st.session_state:
	elapsed = now - st.session_state.last_logged
	if elapsed.total_seconds() > LOG_AFTER:
		requests.post(google_log_url, data={"entry.644797731":"Rerun_Ping"})
		st.session_state.last_logged = now



st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math too!")
