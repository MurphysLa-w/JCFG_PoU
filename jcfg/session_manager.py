# Manages the session history of streamlit
# History is a list with all previous states. Every state is a list containing the equation(str) and the var table(list of dict) in this order

import ast
import streamlit as st
from .telemetry import log
from .utils import ExitCode

class HistoryManager:
	def __init__(self, session_state):
		self._state = session_state
		self._init_defaults()
		
	def _default_state(self):
		return 	[#hist
					[#state
						r"\rho_\text{Wasser} = \frac{m_\text{Wasser}}{V_\text{Wasser}}",
						
						[{"Formelzeichen": r"m_\text{Wasser}", "Einheit": "g", "Messwert": 100.0, "Fehler": 0.1, "Ist Konstant": False},
						{"Formelzeichen": r"V_\text{Wasser}", "Einheit": "ml", "Messwert": 100.0, "Fehler": 0.01, "Ist Konstant": False}]
					]
				]	
	
	def _init_defaults(self):
		if "index" not in self._state:
			log(0)
			self._state.index = 0
		if "history" not in self._state:
			self._state.history = self._default_state()
	
	# Used for getting values
	def index(self):
		return self._state.index
	def current(self):
		return self._state.history[self._state.index]
	def equation(self):
		return self._state.history[self._state.index][0]
	def variables(self):
		return self._state.history[self._state.index][1]
	
	
	def push(self, new_state):
		history = self._state.history
		index = self._state.index
		
		# Delete History that might now be "in the future" as every edit is the latest change and most recent in history
		if self.can_redo():
			history = history[: index + 1]
		history.append(new_state)
		
		# Update and move index
		self._state.history = history
		self._state.index = len(history)-1
		log(self.equation())
	
	
	def can_undo(self):
		return self._state.index > 0
	def can_redo(self):
		return self._state.index < len(self._state.history)-1
	
	
	def undo(self):
		self._state.index -= 1
	def redo(self):
		self._state.index += 1
	
	
	def importString(self, str_import):
		history = self._state.history
		self.str_import = str_import
		try:
			# Get the state sections and read them as csv into a DataFrame and convert to dict, then safe to history and update it
			history.append([self.str_import[2:].split("', [{'Formelzeichen': ")[0].replace("\\\\", "\\"),
							ast.literal_eval(self.str_import.split(self.str_import.split("', [{'Formelzeichen': ")[0])[-1][3:-1])])
		
			self._state.history = history
			self._state.index = len(history)-1
			return True
		except:
			return False
