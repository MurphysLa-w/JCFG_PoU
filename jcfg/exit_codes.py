# ExitCode management

import streamlit as st
from dataclasses import dataclass

@dataclass
class ExitCode:
	code: int					# Codes: 100 warn, 200 error, else info
	args: dict | None = None	# Message arguments, used in render function to insert into the ExitCode message

# First Num defines Level: 0 DEBUG, 1 WARNING, 2 ERROR, 3 SUCCESS, 4+ INFO
EXITCODES_MESSAGES = {
	# Input and Validation
	200:("Die Eingaben sind fehlerhaft und können so nicht verarbeitet werden."),
	201:("Die Gleichung enthält kein/zu viele '=' Zeichen! \n\n Die Gleichung muss nach folgendem Muster aufgebaut sein: '[Größe] = [Formel um Größe zu berechnen]'"),
	202:("Es wurden mehr als 26 Variablen angegeben!"),
	203:("Es wurden keine Variablen angegeben!"),
	204:("Alle Variablen wurden als Konstant gelistet!"),
	205:("Die {index}. Variable in der Tabelle ist unbenannt!"),
	206:("Die {index}. Variable in der Tabelle ('{name}') kommt in der Gleichung nicht vor!"),
	207:("Der Name der {index}. Variable in der Tabelle ('{name}') ist zu kurz! \n\n"+
			"Verlängern Sie z.B. den Namen '{name}' zu '{name}_1' oder verwenden Sie einen anderen."),
	107:("Der Name der {index}. Variable in der Tabelle ('{name}') ist sehr kurz! \n\n"+
			"Verlängern Sie z.B. den Namen '{name}' zu '{name}_1' oder verwenden Sie einen anderen."),
	208:("Die {index}. Variable in der Tabelle ('{name}') ist als Zeichenfolge nicht eindeutig genug, "+
			"da sie bereits im Namen anderer Variablen oder Steuerwörtern aus LaTex (z.B. '\\frac') vorkommt. \n\n"+
			"'{name}' ist u.a. Teil der {bl_index}. Variable '{bl_name}' \n\n"+
			"Verlängern Sie z.B. den Namen '{name}' zu '{name}_1' oder verwenden Sie einen anderen."),
	
	# Refining
	210:("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält"),
	211:("Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält \n\n Liegt der Fehler bei einem fehlerhaften '\\cdot'?"),
	212:("Eine Klammer wurde geöffnet, aber nicht geschlossen"),
	213:("Es ist nicht eindeutig genug, welcher Exponent/Logarythmus wo zu gehört. \n\n Setzen Sie zur Sicherheit um jede Exponentenbasis und jeden logarythmierten Term '()' KLammern um Eindeutigkeit zu schaffen. \n\n - e^{X} + Y -> (e^{X}) + Y \n\n - \\ln{X} + Y -> (\\ln{X}) + Y usw."),
	214:("Die Formel enthält Abschnitte die: \n\n - Rein Formativ \n\n - Falsch geschrieben \n\n - Teil von Variablennamen sind. \n\n Bitte korrigieren Sie den Fehler oder geben sie die Variablen vollständig an. \n\n Der Fehler liegt vor oder am Anfang von: '{errorStr}'"),
	
	# Calculation
	220:("Formel konnte nicht ausgerechnet werden. Prüfen Sie Formel und Variablen."),
	121:("Ergebnis ist Unendlich. Division durch Null?"),
	122:("Ergebnis ist NaN. Fehlen Messwerte oder wird durch Null dividiert?"),
	123:("Die Formel liefert kein eindeutiges Ergebnis. \n\n Lösungen: {solutions}"),
	
	# Program
	230:("Es ist ein Fehler aufgetreten. Melde dies bitte unseren Devs."),
	231:("Import fehlgeschlagen"),
	332:("Erfolgreich gesendet"),
	333:("Erfolgreich gesendet \n\n Wir werden uns baldmöglichst zurückmelden :)"),
	134:("Konnte nicht gesendet werden. Versuchen Sie es später erneut")
}

def render_ExitCode(excode):
	excode_msg = EXITCODES_MESSAGES.get(excode.code, "Es ist ein Fehler aufgetreten. Melde dies bitte unseren Devs.")
	return excode_msg.format(**(excode.args or {}))

def display_ExitCodes(codes, DEBUG):
	critical = False
	for excode in codes:
		if excode.code // 100 == 0:
			if DEBUG:
				st.info(render_ExitCode(excode))
		elif excode.code // 100 == 1:
			if DEBUG:
				st.warning(render_ExitCode(excode) + "\n\n ExitCode: " + str(excode.code), icon="⚠️")
			else:
				st.warning(render_ExitCode(excode), icon="⚠️")
		elif excode.code // 100 == 2:
			if DEBUG:
				st.error(render_ExitCode(excode) + "\n\n ExitCode: " + str(excode.code), icon="🚨")
			else:
				st.error(render_ExitCode(excode), icon="🚨")
			critical = True
		elif excode.code // 100 == 3:
			if DEBUG:
				st.success(render_ExitCode(excode) + "\n\n ExitCode: " + str(excode.code), icon="✅️")
			else:
				st.success(render_ExitCode(excode), icon="✅️")
		else:
			if DEBUG:
				st.info(render_ExitCode(excode) + "\n\n ExitCode: " + str(excode.code), icon="❕️")
			else:
				st.info(render_ExitCode(excode), icon="❕️")
	if critical:
		st.error("Korrigieren Sie zuerst die Fehler in der Formel und der Tabelle", icon="🚨")
	
	return critical
