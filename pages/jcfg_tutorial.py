# Streamlit-App for JCFG Propagation of Uncertainty Calculator

import time
import pandas as pd
import streamlit as st

from jcfg.telemetry import submit_bug_report
from jcfg.core import Variable, PoUInput, PoUOutput, PoUEngine
from jcfg.session_manager import HistoryManager
from jcfg.utils import to_float_safe
from jcfg.exit_codes import ExitCode, display_ExitCodes

# Functions to manipulate the state
def state():
	return st.session_state.tut_state
def is_state(min_state, max_state=None):
	if max_state == None:
		return st.session_state.tut_state == min_state
	else:
		return st.session_state.tut_state in range(min_state, max_state+1)
def goto(next):
	st.session_state.tut_state = next
	st.rerun()

# Set Up History and state
hist = HistoryManager(st.session_state)
if "tut_state" not in st.session_state:
	goto(-1)
if is_state(0):
	hist.reset_to("tutorial")

# Page Header
st.set_page_config(page_title="JCFG")
st.title("Tutorial zum Rechner")
header_col1, header_col2 = st.columns([0.75, 0.25] ,vertical_alignment="center")
header_col1.info("Dies ist das Tutorial. Zur Rückkehr zum Rechner bitte folgenden Button verwenden.")

# Return Condition with button and state
if header_col2.container(horizontal_alignment="right").button("Zurück zum Rechner", type="primary") or state() < -1:
	hist.reset_to("default")
	st.session_state.tut_state = -1
	st.switch_page("pages/jcfg_calculator.py")




# Make the Chat
chat = st.container(border=True)

# All Chat messages called by their respective state
@st.dialog("I. Input", dismissible=False)
def tut_input():
	dchat = st.container(border=True)
	msg = dchat.chat_message("assistant")
	msg.markdown("Dies ist das Tutorial zum JCFG-Fehlerrechner.\n\nDu kommst im Tutorial voran indem du :orange-background[markierte Aufgaben] löst oder mit diesen Buttons auf meine Nachrichten :orange-background[antwortest]")
	if dchat.chat_message("human").button("Verstanden", disabled=state()!=-1):
		goto(0)

if is_state(-1):
	tut_input()

if is_state(0):
	msg = chat.chat_message("assistant")
	msg.write("Hallo\n\n Dieser Rechner soll die Berechnung und Darstellung der Gauß'schen Fehlerfortpflanzung in LaTeX vereinfachen. \n\n Er richtet sich damit vorrangig an LaTeX-Nutzer.")
	with chat.spinner("..."):
		time.sleep(1)
	if chat.chat_message("human").button("Ich benutze LaTeX für meine Formeln oder habe bereits grundlegende Kenntnisse davon."):
		goto(1)

if is_state(1,3):
	msg = chat.chat_message("assistant")
	msg.write("Sehr gut.\n\n Berechnen wir also den Fehler einer Größe an einem Beispiel:")
	msg.container(border=True).write("'Eine Konzentration 𝑐 wird als Quotient aus Stoffmenge 𝑛 und Volumen 𝑉 bestimmt. Sowohl Stoffmenge als auch Volumen sind mit einem Fehler (Δ𝑛 und Δ𝑉 ) behaftet.'")
	if chat.chat_message("human").button("Ok, weiter...", disabled=state()!=1):
		goto(2)

if is_state(2,3):
	msg = chat.chat_message("assistant")
	msg.write("Die Gleichung für 𝑐 sieht in LaTeX so aus:")
	msg.container(border=True).latex(r"c = \frac{n}{V}")
	msg.write("... und wird durch diesen Code generiert:")
	msg.code(r"c = \frac{n}{V}", language="latex")
	if chat.chat_message("human").button("Verstanden...", disabled=state()!=2):
		goto(3)

if is_state(3):
	msg = chat.chat_message("assistant")
	msg.markdown("Der Fehlerrechner nimmt zur Berechnung diese Gleichung in LaTeX-Code als Input. :orange-background[Kopiere deine Gleichung aus dem Code-Feld oben in das Input-Feld unten.]")

@st.dialog("II. Variablen")
def tut_variables():
	dchat = st.container(border=True)
	msg = dchat.chat_message("assistant")
	msg.write("Gut gemacht.")
	msg.write("Nun weiß der Rechner allerdings noch nicht, welcher Teil der Gleichung unsere Variablen sind. Daher müssen wir 𝑛 und 𝑉 noch einmal separat angeben.")
	msg.write("Dies tun wir in der folgenden Variablen-Tabelle:")
	if dchat.chat_message("human").button("Verstanden...", disabled=state()!=4):
		goto(5)

if is_state(4):
	tut_variables()

if is_state(5):
	msg = chat.chat_message("assistant")
	msg.write("Sehr gut.")
	msg.markdown(":orange-background[Gib nun in der Ersten Spalte 'Formelzeichen' die Namen der Variablen an, sodass in der ersten Zelle n und in der darunter V steht.]")
	msg.write("Die anderen Spalten ignorieren wir vorerst...")
	msg.write("- Du kannst Zellen bearbeiten indem du auf sie klickst.\n\n- Du kannst Reihen hinzufügen indem du auf die unterste freie Reihe klickst.\n\n- Du kannst Reihen löschen indem du sie am linken Rand der Tabelle markierst und dann auf den Mülleimer oben recht an der Tabelle klickst.")
		
@st.dialog("III. Fehlermeldungen")
def tut_exitcodes():
	dchat = st.container(border=True)
	msg = dchat.chat_message("assistant")
	msg.write("Sehr gut.")
	msg.write("Um deine Fehler in deinen Inputs schnell zu erkennen, gibt dir der Rechner Fehlermeldungen zur Seite. \n\nSo sieht eine Fehlermeldung aus: Rote sind kritisch und müssen gelöst werden, Gelbe sind Warnungen und nicht kritisch")
	dchat.error("Ich bin eine kritische Testmeldung. Ein Problem muss erst behoben werden, bevor der Input weiterverarbeitet werden kann", icon="🚨️")
	
	if dchat.chat_message("human").button("Weiterlesen...", disabled=state()!=6):
		goto(7)
		
if is_state(6):
	tut_exitcodes()

if is_state(7,8):
	msg = chat.chat_message("assistant")
	msg.write("Hier kommen auch schon Fehler:")
	msg.markdown("Deine Variablennamen sind zu kurz! Lies die Fehlermeldungen die gleich erscheinen und :orange-background[versuche eine Lösung für das Problem zu finden.]")
	msg.write("Wenn du die Lösung brauchst kannst du aufgeben und 'Lösung ansehen' drücken")
	if chat.chat_message("human").button("Na gut, ich versuche es...", disabled=state()!=7):
		goto(8)
	
if is_state(8,9):
	msg = chat.chat_message("human")
	msg.write("Ich gebe auf: ")
	if msg.button("Lösung ansehen", disabled=state()!=8):
		goto(9)
	
if is_state(9):
	msg = chat.chat_message("assistant")
	msg.write("Schritt 1: Du musstest die erste Variable n zu n_1 verlängern. \n\n Schritt 2: Nun musste der Name n auch noch in der Gleichung zu n_1 geändert werden.")
	if chat.chat_message("human").button("Ok...", disabled=state()!=9):
		hist.importString(r"['c = \\frac{n_1}{V_1}', [{'Formelzeichen': 'n_1', 'Einheit': 'mol', 'Messwert': 0.25, 'Fehler': 0.05, 'Ist Konstant': False}, {'Formelzeichen': 'V_1', 'Einheit': 'L', 'Messwert': 0.5, 'Fehler': 0.01, 'Ist Konstant': False}]]")
		goto(11)

@st.dialog("IV. Modi")
def tut_modi():
	dchat = st.container(border=True)
	msg = dchat.chat_message("assistant")
	msg.write("Großartig gelöst.")
	msg.write("Nun wird die Formel für den Fehler von selbst berechnet und in LaTeX-Code dargestellt, du findest sie unten.")
	if dchat.chat_message("human").button("Ansehen...", disabled=state()!=10):
		goto(11)
		
if is_state(10):
	tut_modi()

if is_state(11):
	msg = chat.chat_message("assistant")
	msg.write("Nun wird die Formel für den Fehler von selbst berechnet und in LaTeX-Code dargestellt, du findest sie unten.")
	if chat.chat_message("human").button("Cool...", disabled=state()!=11):
		goto(12)
	
if is_state(12,13):
	msg = chat.chat_message("assistant")
	msg.write("Natürlich kann der Rechner noch mehr: Wenn wir ihm Werte und Einheiten geben, dann können wir die Formel auch mit Werten darstellen und schließlich lösen.")
	msg.write("Ich habe dir hierfür bereits Werte und Einheiten in die Variablen-Tabelle eingetragen. In der Praxis müssen diese von dir eingefügt werden.")
	msg.write("Die letzte Spalte 'Ist Konstant' ist für Konstanten und Variablen ohne Fehler wie der Allgemeinen Gaskonstante R. Hier kann R in der Gleichung verwendet werden, es wird aber nicht nach R abgeleitet.")
	if chat.chat_message("human").button("Ansehen...", disabled=state()!=12):
		hist.importString(r"['c = \\frac{n_1}{V_1}', [{'Formelzeichen': 'n_1', 'Einheit': 'mol', 'Messwert': 0.25, 'Fehler': 0.05, 'Ist Konstant': False}, {'Formelzeichen': 'V_1', 'Einheit': 'L', 'Messwert': 0.5, 'Fehler': 0.01, 'Ist Konstant': False}]]")
		goto(13)
	if is_state(13) and chat.chat_message("human").button("Weiter...", disabled=state()!=13):
		goto(14)

if is_state(14):
	msg = chat.chat_message("assistant")
	msg.write("Bisher habe ich entschieden was du siehst.")
	msg.write("Um selbst Teile ein und auszublenden nutze die Seitenleiste. Hier findest du Schalter für die einzelenen Anzeige-Modi, einen Werkzeugkasten um Eingaben Rückgängig zu machen, eine DEBUG-Funktion um mehr Infos zu bekommen und eine Möglichkeit uns zu kontaktieren und Bugs zu melden oder Hilfe zu bekommen.")
	msg.write("Du kannst die Seitenleiste mit den Pfeilen oben rechts ein- und ausklappen.")
	if chat.chat_message("human").button("Ansehen...", disabled=state()!=14):
		goto(15)


# Setting modes if the Button doesnt exist at the time
if state() <= 11:
	modeD = modeV = modeC = False
	
if state() <= 14:
		DEBUG=False
		undo=False

if is_state(11,12):
	modeD = True
	modeV = modeC = False
	
if is_state(13,14):
	modeD = modeV = modeC = True



if state() >= 3:
	st.subheader("Input Gleichung")
	equation = st.text_input("Gleichung für die Größe, für welche der Fehler berechnet werden soll:", hist.equation())
	st.latex(equation)
	
	if is_state(3) and equation.replace(" ", "") == r"c=\frac{n}{V}":
		goto(4)
		
if state() >= 5:
	# Table for Var Input with list of dict from state
	st.subheader("Variablen")
	st.text("Liste aller Variablennamen welche in der Gleichung vorkommen:")
	edited_df = st.data_editor(pd.DataFrame(hist.variables()), num_rows="dynamic")
	
	# Compress back to dictlist and clean from empty rows
	dictVar = edited_df.to_dict(orient='records')
	cleaned_vars = [row for row in dictVar if not (row["Formelzeichen"] is None and row["Einheit"] is None and pd.isna(row["Messwert"]) and pd.isna(row["Fehler"]) and row["Ist Konstant"] is None)]
	
	# Get the new current state
	new_state = [equation, cleaned_vars]
	
if is_state(15):
	### Sidebar
	st.sidebar.info("TUTORIAL MODUS")
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
	DEBUG = st.sidebar.toggle("Debug-Modus")
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
	def bug_dialog(opt_index=0):
		# Setting Up the Dialog
		with st.form("Bug Melden"):
			bug_kind = st.selectbox("Art:", ("Hilfe/Support", "Feedback", "Falsches Ergebnis", "Eingabe-/Verarbeitungsfehler", "Sonstiges"),index=opt_index)
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
	
if is_state(5,14):
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

if state() >= 5:
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
	
	
	if is_state(5) and [var.name for var in variables] == ["n", "V"]:
		goto(6)
		
if state() >= 8:
	# Initialize the Engine
	engine = PoUEngine(input_data)
	
	# Validate Input, find Errors in User Input
	codes = engine.validate_input()
	if display_ExitCodes(codes, DEBUG):
		st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math	too!")
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
	
	if is_state(8,9) and str(engine.symbol_expr) == "roca/rocb":
		goto(10)

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
	if DEBUG: st.info("Vor Einsetzen:   " + str(engine.cumul_uncert))
	if DEBUG: st.info("Nach Einsetzen:   " + str(engine.result_str))
	st.latex(PoU_Calc.latex_display)
	st.code(PoU_Calc.latex_code, language="latex")
	display_ExitCodes(codes, DEBUG)

# Message Pointer
if is_state(7) or is_state(11) or is_state(13) or is_state(15):
	st.success("Neue Nachricht oben", icon="☝️")
	
if is_state(15):
	msg = chat.chat_message("assistant")
	msg.write("Hiermit ist das Tutorial abgeschlossen, sieh dich gerne noch um. \n\n Wenn du fertig bist, kehre hier zurück zum Rechner.")
	msg = chat.chat_message("human")
	if msg.button("Tutorial beenden und zurückkehren", disabled=state()!=15):
		goto(-2)
	if msg.button("Feedback geben", type="primary"):
		bug_dialog(1)

st.caption("This tool is for informational and educational purposes only. It cannot be held responsible for invalid results. Do your own math too!")
