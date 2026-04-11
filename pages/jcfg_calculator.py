# Streamlit-App for JCFG Propagation of Uncertainty Calculator

__version__ = "1.7.1-beta"

import pandas as pd
import streamlit as st

from jcfg.telemetry import submit_bug_report
from jcfg.core import Variable, PoUInput, PoUOutput, PoUEngine
from jcfg.session_manager import HistoryManager
from jcfg.utils import to_float_safe
from jcfg.exit_codes import ExitCode, display_ExitCodes

# Page Header
st.set_page_config(page_title="JCFG")
st.title("Fehlerrechner nach Gauß")
header_col1, header_col2 = st.columns([0.75, 0.25], vertical_alignment="center")
header_col1.text("V  "+ __version__ +"\nGauß'sche Fehlerberechnung mit LaTeX-Ein- und Ausgabe")

@st.dialog("Tutorial Starten?")
def tutorial_dialog():
	st.write("Neu hier?\n\nStarte das Tutorial für den Rechner und lerne die grundlegenden Funktionen\n\nAchtung, das Starten des Tutorials löscht alle Eingaben im Rechner")
	if st.button("Tutorial starten"): st.switch_page("pages/jcfg_tutorial.py")
if header_col2.container(horizontal_alignment="right").button("Tutorial"):
	tutorial_dialog()

# Set Up History
hist = HistoryManager(st.session_state)

### Getting the User Input
## Displaying current state
# Equation Input with str from state
st.subheader("Input Gleichung")
equation = st.text_input("Gleichung für die Größe, für welche der Fehler berechnet werden soll:", hist.equation())
st.latex(equation)

# Table for Var Input with list of dict from state
st.subheader("Variablen")
st.text("Liste aller Variablennamen welche in der Gleichung vorkommen:")
edited_df = st.data_editor(pd.DataFrame(hist.variables()), num_rows="dynamic")

# Compress back to dictlist and clean from empty rows
dictVar = edited_df.to_dict(orient='records')
cleaned_vars = [row for row in dictVar if not (row["Formelzeichen"] is None and row["Einheit"] is None and pd.isna(row["Messwert"]) and pd.isna(row["Fehler"]) and row["Ist Konstant"] is None)]

# Get the new current state
new_state = [equation, cleaned_vars]


### Sidebar
st.sidebar.header("Editor")
DEBUG = False
DEVMODE = False
str_import = ""

## Editor
editor = st.sidebar.expander("Werkzeuge", True)
editor_col1, editor_col2, editor_col3, editor_col4 = editor.columns(4 ,vertical_alignment="center")

## Mode Selector
st.sidebar.header("Modi")
modeS = st.sidebar.toggle("Ableitungen nach allen Variablen")
modeR = st.sidebar.toggle("Formel in Rohform")
modeD = st.sidebar.toggle("Formel mit Ableitungen", True)
modeV = st.sidebar.toggle("Formel mit Fehlerwerten", True)
modeC = st.sidebar.toggle("Errechneter Fehler", True)

## Debug
st.sidebar.subheader("DEBUG")
DEBUG = st.sidebar.toggle("Debug Modus")
DEVMODE = False
if DEBUG:
	DEVMODE = st.sidebar.toggle("Entwickleroptionen")
	st.info("DEBUG: Aktiv")
	st.sidebar.info("DEBUG: Aktiv")

# Tools in Editor
undo = editor_col1.button("",icon=":material/undo:", help="Rückgängig", 		use_container_width=True, disabled=not hist.can_undo())
redo = editor_col2.button("",icon=":material/redo:", help="Wiederherstellen", 	use_container_width=True, disabled=not hist.can_redo())
export_inputs = editor_col3.button("",icon=":material/output_circle:", help="Exportiere Eingaben als String", use_container_width=True, disabled=not DEVMODE)
import_inputs = editor_col4.button("",icon=":material/input_circle:", help="Importiere Eingaben als String", use_container_width=True, disabled=not DEVMODE)

## Functionality to the sidebar
# Undo / Redo
if undo and hist.can_undo():
	hist.undo()
	st.rerun()

if redo and hist.can_redo():
	hist.redo()
	st.rerun()

# Push new if changes have been made
if not undo and str(hist.current()) != str(new_state) and len(edited_df.columns) == 5:
	# Push and rerun to make sure its the new base state for the st.data_editor
	hist.push(new_state)
	st.rerun()
	
# Fix if user has broken the dataframe for Some Reason
elif len(edited_df.columns) != 5:
	hist.undo()
	hist.push(hist.current())
	st.rerun()

# Export / Import
if export_inputs:
	editor.text_input("Import/Export als String", value=str(hist.current()))
elif DEVMODE:
	str_import = editor.text_input("Import/Export als String", placeholder="Importiere Eingaben")

if len(str_import) != 0:
	editor.warning("Importiere nur wenn du weißt was du tust", icon="❗️")
if len(str_import) != 0 and import_inputs:
	if hist.importString(str_import):
		st.rerun()
	else:
		# Import failed
		display_ExitCodes([ExitCode(231)], DEBUG)

## Bug-Reporting
# Dialog window for the report
@st.dialog("Feedback / Bug melden")
def bug_dialog():
	# Setting Up the Dialog
	with st.form("Bug Melden"):
		bug_kind = st.selectbox("Art:", ("Hilfe/Support", "Feedback", "Falsches Ergebnis", "Eingabe-/Verarbeitungsfehler", "Sonstiges"),)
		bug_desc = st.text_area("Eigene Beschreibung:")
		bug_email = st.text_input("Email Adresse für Rückmeldungen/Hilfe", placeholder=("(Optional)"))
		submit = st.form_submit_button("Absenden")
		# Sending the data
		if submit:
			display_ExitCodes(submit_bug_report(bug_kind, bug_desc, bug_email, hist.current()), DEBUG)
	st.caption("Über diesen Dialog kann Kontakt mit den Entwicklern aufgenommen werden um Bugs zu melden, Feedback zu geben oder Hilfe zu bekommen. Wenn Sie eine Rückmeldung erhalten wollen, geben Sie bitte eine E-Mail Adresse an. Danke, dass Sie zur Verbesserung dises Tools beitragen.")	
		
# Button to call the dialog
if st.sidebar.button("Support / Bug Melden", type="primary"):
	bug_dialog()

# Show additional Infos in DEVMODE
# Show History
if DEVMODE:
	with st.expander("DEBUG Verlauf"):
		st.info("Aktueller Index:   " + str(hist.index()))
		st.json(st.session_state.history, expanded=1)


### Retrieve and Process the User Input
variables = []
for row in cleaned_vars:
	variables.append(
		Variable(
			name=row["Formelzeichen"],
			unit=row["Einheit"],
			value=to_float_safe(row["Messwert"]),
			uncert=to_float_safe(row["Fehler"]),
			const=row["Ist Konstant"]
		)
	)
input_data = PoUInput(
	equation=equation,
	variables=variables
)

# Display Variables for visual error recognition
with st.expander("Variablen in LaTex Form", True):
	for var in variables:
		st.latex(str(var.name) + r"~/~\mathrm{" + str(var.unit) + r"}=" + str(var.value) + r" \pm " + str(var.uncert))

# Initialize the Engine
engine = PoUEngine(input_data)

# Validate Input, find Errors in User Input
codes = engine.validate_input()
if display_ExitCodes(codes, DEBUG):
	st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math too!")
	st.stop()

# Refine Input, find remaining Errors
codes = engine.refine_input()
if DEBUG: st.info("Vor Aufbereitung:   " + str(engine.expression))
bug_expression = engine.expression
if DEBUG: st.info("Nach Aufbereitung:   " + str(engine.norm_expr))

if display_ExitCodes(codes, DEBUG):
	st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math too!")
	st.stop()

if DEBUG: st.info("Nach Übersetzung:   " + str(engine.symbol_expr))

## The Modus Operandi
# Print the Singular Derivatives for each Variable
if modeS:
	st.subheader("Einzelableitungen")
	 
	for sDeriv in engine.modeS():
		# Print
		st.latex(sDeriv.latex_display)
		st.code(sDeriv.latex_code, language="latex")
		
# Print the Raw PoU Formula		
if modeR:
	st.subheader("Rohformel")
	PoU_Raw, codes = engine.modeR()
	st.latex(PoU_Raw.latex_display)
	st.code(PoU_Raw.latex_code, language="latex")
	display_ExitCodes(codes, DEBUG)

# Print the PoU Formula with Derivatives
if modeD or modeV or modeC: # Required for V, C
	PoU_Deriv, codes = engine.modeD()
	if modeD:
		st.subheader("Formel mit Ableitungen")
		if DEBUG: st.info("Deriv:   " + str(engine.PoU_Diff))
		st.latex(PoU_Deriv.latex_display)
		st.code(PoU_Deriv.latex_code, language="latex")
		display_ExitCodes(codes, DEBUG)

# Print the PoU Formula with Values
if modeV:
	st.subheader("Formel mit Fehlerwerten")
	PoU_Val, codes = engine.modeV()
	st.latex(PoU_Val.latex_display)
	st.code(PoU_Val.latex_code, language="latex")
	display_ExitCodes(codes, DEBUG)

# Calculate the Uncertainty
if modeC:
	st.subheader("Errechneter Fehler")
	PoU_Calc, codes = engine.modeC()
	if DEBUG: st.info("Vor Einsetzen:   ```" + str(engine.cumul_uncert)+"```")
	if DEBUG: st.info("Nach Einsetzen:   " + str(engine.result_str))
	st.latex(PoU_Calc.latex_display)
	st.code(PoU_Calc.latex_code, language="latex")
	st.code(PoU_Calc.expr_code)
	st.caption(":violet-badge[Beta] Ausdruck für die Berechnung mit variablen Messwerten")
	display_ExitCodes(codes, DEBUG)

st.space("small")
st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math too!")
