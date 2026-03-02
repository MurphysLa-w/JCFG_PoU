# Core functions and logic for JCFG

import re as regex
#import sympy as sp
from typing import List
from dataclasses import dataclass
from .utils import ExitCode, to_str_safe
from sympy import symbols, latex, simplify, diff
from sympy.parsing.latex import parse_latex
from lark.exceptions import UnexpectedEOF, UnexpectedCharacters

@dataclass
class Variable:
	name: str
	unit: str
	value: float #"(12.34)"
	uncert: float #"(12.34)"
	const: bool

@dataclass
class PoUInput:
	equation: str
	variables: List[Variable]

@dataclass
class PoUOutput:
	latex_display: str
	latex_code: str

class PoUEngine:
	LATEX_RESERVED = [
		r"\cdot", r"\frac", r"\mathit", r"\log", r"\ln", r"e^",
		r"\sin", r"\cos", r"\tan", r"\cot", r"\sec", r"\csc",
		r"\arcsin", r"\arccos", r"\arctan", r"\sinh", r"\cosh",
		r"\tanh", r"\exp", r"\sqrt", r"\left", r"\right", r"\theta",
		r"\pi", r"\sum", r"\prod", r"\int", r"\lim", r"\infty",
		r"\partial", r"\Delta", r"\alpha", r"\beta", r"\gamma", r"\epsilon",
	]
	nAdd = "roc"
	
	def __init__(self, input_data):
		self.input = input_data
		self.blacklist = self.init_blacklist()
		
		# Input.equation is split into two terms (res_name, expression)
		self.res_name = ""
		self.expression = ""
		self.norm_expr = ""
		self.symbol_dict = {}
		self.symbol_expr = None
		
		self.PoU_Diff = ""
		self.PoU_Val = ""
		self.PoU_Calc = ""
		
		self.cumul_uncert = 0
		self.result_str = ""
	
	def init_blacklist(self):
		blacklist = []
		for var in self.input.variables:
			blacklist.append(var.name)
		for i in range(len(self.input.variables)):
			blacklist.append(r"\mathit{"+self.nAdd+chr(i+97)+"}")
		blacklist += self.LATEX_RESERVED
		return blacklist
	
	def validate_input(self):
		codes = []
		if self.input.equation.count("=") != 1:
			codes.append(ExitCode(201, "Die Formel enthält kein/zu viele '=' Zeichen! \n\n Die Formel muss nach folgendem Muster aufgebaut sein: '[Größe] = [Formel um Größe zu berechnen]'"))
		if len(self.input.variables) >= 26:
			codes.append(ExitCode(202,"Es wurden mehr als 26 Variablen angegeben!"))
		if len(self.input.variables) == 0:
			codes.append(ExitCode(203,"Es wurden keine Variablen angegeben!"))
		elif all(var.const for var in self.input.variables):
			codes.append(ExitCode(204,"Alle Variablen wurden als Konstant gelistet!"))
		for i, var in enumerate(self.input.variables, start=1):
			if var.name == None or var.name in ["", " ", "  "]:
				codes.append(ExitCode(204,"Die " + str(i) + ". Variable in der Tabelle ist unbenannt!"))
			elif var.name not in self.input.equation:
				codes.append(ExitCode(206,"Die " + str(i) + ". Variabl ein der Tabelle ('"+str(var.name)+"') kommt in der Formel nicht vor!"))
			elif len(var.name) == 1 and 'a' <= var.name <= 'z':
				codes.append(ExitCode(205,"Der Name der " + str(i) + ". Variable in der Tabelle ('"+str(var.name)+"') ist zu kurz! \n\n"+
					"Verlängern Sie z.B. den Namen '"+str(var.name)+"' zu '"+str(var.name)+"_1' oder verwenden Sie einen anderen."))
			else:
				match = next(((bLi, bLname) for bLi, bLname in enumerate(self.blacklist, start=1) if (var.name in bLname) and (i != bLi)), None)
				if match:
					bLi, bLname = match
					codes.append(ExitCode(207,"Die " + str(i) + ". Variable in der Tabelle ('"+str(var.name)+"') ist als Zeichenfolge nicht eindeutig genug, "+
						"da sie bereits im Namen anderer Variablen oder Steuerwörtern aus LaTex (z.B. '\\frac') vorkommt. \n\n"+
						"'"+str(var.name)+"' ist u.a. Teil der "+str(bLi)+". Variable '"+bLname+"' \n\n"+
						"Verlängern Sie z.B. den Namen '"+str(var.name)+"' zu '"+str(var.name)+"_1' oder verwenden Sie einen anderen."))
				elif len(var.name) == 1:
					codes.append(ExitCode(105,"Der Name der " + str(i) + ". Variable in der Tabelle ('"+str(var.name)+"') ist sehr kurz! \n\n"+
						"Verlängern Sie z.B. den Namen '"+str(var.name)+"' zu '"+str(var.name)+"_1' oder verwenden Sie einen anderen."))
		return codes
		
	def refine_input(self):
		codes = []
		# Split Equation and format
		self.res_name, self.expression = self.input.equation.split("=")
		
		# Normalize Expression (Replace Names wth symbols, remove unknown symbols)
		self.norm_expr = self.expression
		for i, var in enumerate(self.input.variables):
			self.norm_expr = self.norm_expr.replace(var.name, r"\mathit{" + self.nAdd + chr(i+97) + "}")
		self.norm_expr = self.norm_expr.replace(r"\left(", "(").replace(r"\right)", ")")	#Replace \left( \right) with ()
		self.norm_expr = self.norm_expr.replace("e^", r"\exp")								#Replace e^ with \exp to make an exponential function
		
		# Process Names are put in a dictionary
		self.symbol_dict = {self.nAdd+chr(i+97): symbols(self.nAdd+chr(i+97)) for i, var in enumerate(self.input.variables)}
		self.numeric_dict = {self.symbol_dict[self.nAdd+chr(i+97)]: var.value for i, var in enumerate(self.input.variables)}#if var.value is not None
		
		# Make Symbolic Expression (Translate with Lark)
		try:
			self.symbol_expr = parse_latex(self.norm_expr, backend="lark")
			
			# Catching the "dx-Tuple Bug"
			# A 'd' before any character makes a diff and creates a tuple unsuable further on
			try:
				# Try differentiating
				diff(self.symbol_expr, self.symbol_dict[self.nAdd+'a'])
				
			except sp.SympifyError:
				codes.append(ExitCode(213, "Es ist nicht eindeutig genug, welcher Exponent/Logarythmus wo zu gehört. \n\n Setzen Sie zur Sicherheit um jede Exponentenbasis und jeden logarythmierten Term '()' KLammern um Eindeutigkeit zu schaffen. \n\n - e^{X} + Y -> (e^{X}) + Y \n\n - \\ln{X} + Y -> (\\ln{X}) + Y usw."))
			# If thats not possible(i.e symbol_expr has become a tuple) catch it
			except Exception as e:
				codes.append(ExitCode(211, "Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält \n\n Liegt der Fehler bei einem fehlerhaften '\\cdot'?"))
			
		except UnexpectedEOF as e:
			codes.append(ExitCode(212, "Eine Klammer wurde geöffnet, aber nicht geschlossen"))
			print(self.norm_expr)
			print(e)
			
		except UnexpectedCharacters as e:
			errorStr = str(e).split("\n")[2][int(len(str(e).split("\n")[3])-1):]
			for i, var in enumerate(self.input.variables):
				errorStr = errorStr.replace(r"\mathit{"+self.nAdd+chr(i+97)+"}", var.name)
			codes.append(ExitCode(212, "Die Formel enthält Abschnitte die: \n\n - Rein Formativ \n\n - Falsch geschrieben \n\n - Teil von Variablennamen sind. \n\n Bitte korrigieren Sie den Fehler oder geben sie die Variablen vollständig an. \n\n Der Fehler liegt vor oder am Anfang von: '" + errorStr + "'"))
		
		except sp.SympifyError:
			codes.append(ExitCode(213, "Es ist nicht eindeutig genug, welcher Exponent/Logarythmus wo zu gehört. \n\n Setzen Sie zur Sicherheit um jede Exponentenbasis und jeden logarythmierten Term '()' KLammern um Eindeutigkeit zu schaffen. \n\n - e^{X} + Y -> (e^{X}) + Y \n\n - \\ln{X} + Y -> (\\ln{X}) + Y usw."))
		
		except:
			codes.append(ExitCode(210, "Die Formel konnte nicht verarbeitet werden, es kann sein, dass sie Fehler enthält"))
		
		return codes
	
	def modeS(self):
		all_singleDerivs = []
		# Derive for every var (skip Constants)
		print(self.input.variables)
		for i, var in enumerate(self.input.variables):
			if var.const:
				continue
			# Differentiate, Simplify and parse back into latex
			singleDeriv = latex(simplify(diff(self.symbol_expr, self.symbol_dict[self.nAdd+chr(i+97)])))
			
			# Refining
			singleDeriv = regex.sub(r"(?<=roc[a-z]) (?=roc[a-z])", r" \\cdot " , singleDeriv)		#Add * between rocX and rocY
			singleDeriv = regex.sub(r"(?<=\^\{\d\}) (?=\(?roc[a-z])", r" \\cdot " , singleDeriv)	#Add * between ^{any number} and rocX
			singleDeriv = singleDeriv.replace(".", ",").replace("log", "ln")						#Converting to German notation
			
			# Reintroduce the Original Var Names
			for j, varj in enumerate(self.input.variables):
				singleDeriv = singleDeriv.replace(self.nAdd+chr(j+97), varj.name)
			latex_display = r"\begin{equation}\frac{\partial " + self.res_name + r"}{\partial " + var.name + "} = " + singleDeriv + r" \notag \end{equation}"
			latex_code = r"\begin{equation}\frac{\partial " + self.res_name + r"}{\partial " + var.name + "} = " + singleDeriv + r" \end{equation}"
			all_singleDerivs.append(PoUOutput(latex_display=latex_display, latex_code=latex_code))
		return all_singleDerivs
	
	def modeR(self):
		codes = []
		PoU_Raw = r"\begin{equation} \Delta " + self.res_name + r" = \pm\sqrt{ \begin{split} &"
		for i, var in enumerate(self.input.variables):
			if var.const: # Don't derive for constants
				continue
			PoU_Raw += r"\left(\frac{\partial " + self.res_name + r"}{\partial " + var.name + r"}\Delta " + var.name + r"\right)^{2} \\ &+ "
		
		# Cut the last three chars "&+ " and add the end commands
		latex_display = PoU_Raw[:-3] + r"\end{split}} \notag \end{equation}"
		latex_code = PoU_Raw[:-3] + r"\end{split}} \end{equation}"
		return	PoUOutput(latex_display=latex_display, latex_code=latex_code), codes
	
	def modeD(self):
		codes = []
		PoU_Diff = r"\pm\sqrt{ \begin{split} &"
		for i, var in enumerate(self.input.variables):
			if var.const:
				continue
			PoU_Diff += r"\left(" + str(latex(simplify(diff(self.symbol_expr, self.symbol_dict[self.nAdd+chr(i+97)])))) + r"\Delta " + self.nAdd+chr(i+97) + r"\right)^{2} \\ &+ "
		PoU_Diff = PoU_Diff[:-7] + r"\end{split} }"
		
		# Refining
		PoU_Diff = regex.sub(r"(?<=roc[a-z]) (?=roc[a-z])", r" \\cdot " , PoU_Diff)		#Add * beteen two vars
		PoU_Diff = regex.sub(r"(?<=\^\{\d\}) (?=\(?roc[a-z])", r" \\cdot " , PoU_Diff)	#Add * between ^{any number}
		PoU_Diff = PoU_Diff.replace(".", ",").replace("log", "ln")
		
		# Create Copies for later uses
		self.PoU_Diff = PoU_Diff
		self.PoU_Val = PoU_Diff
		self.PoU_Calc = PoU_Diff
		
		# Reintroduce the Original Var Names
		for i, var in enumerate(self.input.variables):
			PoU_Diff = PoU_Diff.replace(self.nAdd+chr(i+97), var.name)
		
		latex_display = r"\begin{equation} \Delta " + self.res_name + " = " + PoU_Diff + r" \notag \end{equation}"
		latex_code = r"\begin{equation} \Delta " + self.res_name + " = " + PoU_Diff + r"\end{equation}" 
		return	PoUOutput(latex_display=latex_display, latex_code=latex_code), codes
		
	def modeV(self):
		PoU_Val = self.PoU_Val
		codes = []
		
		# Replace var names with their values and units, same for the uncertainties (preceeded by \Delta)
		for i, var in enumerate(self.input.variables):
			PoU_Val = PoU_Val.replace(r"\Delta " + self.nAdd+chr(i+97), r"\cdot" + to_str_safe(var.uncert) + r" \mathrm{" + str(var.unit) + "}")
			PoU_Val = PoU_Val.replace(self.nAdd+chr(i+97), to_str_safe(var.value) + r" \mathrm{" + str(var.unit) + "}")
		
		# Refining
		PoU_Val = regex.sub(r"(?<=\d) (?=\d)", r" \\cdot " , PoU_Val)	#Replace spaces between numbers with a \cdot
		PoU_Val = PoU_Val.replace(".", ",").replace("log", "ln")
		
		latex_display = r"\begin{equation} \Delta " + self.res_name + " = " + PoU_Val + r" \notag \end{equation}"
		latex_code = r"\begin{equation} \Delta "  + self.res_name + " = " + PoU_Val + r"\end{equation}"
		
		if "nan" in PoU_Val:
			codes.append(ExitCode(121, "Nan in der Formel gefunden! Überprüfen sie ob Messwerte fehlen."))
		return PoUOutput(latex_display=latex_display, latex_code=latex_code), codes
		
	def modeC(self):
		codes = []
		latex_display = r"\begin{equation} \Delta " + self.res_name + r" = \pm \text{NaN} \notag \end{equation}"
		latex_code = r"\begin{equation} \Delta " + self.res_name + r" = \pm \text{NaN} \end{equation}"
		
		try:
			for i, var in enumerate(self.input.variables):
				deriv = diff(self.symbol_expr, self.symbol_dict[self.nAdd+chr(i+97)])
				self.cumul_uncert += (deriv * var.uncert)**2
			self.result_str = to_str_safe(self.cumul_uncert.subs(self.numeric_dict))
			
			
			if "zoo" in self.result_str:
				codes.append(ExitCode(123, "Ergebnis ist Unendlich. Division durch Null?"))
			if "nan" in self.result_str:
				codes.append(ExitCode(121, "Ergebnis ist NaN. Fehlen Messwerte oder wird durch Null dividiert?"))
			if "Tree" in self.result_str:
				codes.append(ExitCode(122, "Die Formel liefert kein eindeutiges Ergebnis. \n\n Lösungen: " + self.result_str.replace("Tree('_ambig', ","")[:-1]))
			else:
				latex_display = r"\begin{equation} \Delta " + self.res_name + r" = \pm " + self.result_str.replace(".", ",") + r" \notag \end{equation}"
				latex_code = r"\begin{equation} \Delta " + self.res_name + r" = \pm " + self.result_str.replace(".", ",") + r"\end{equation}"
		except Exception as e:
			codes.append(ExitCode(220, "Formel konnte nicht ausgerechnet werden. Prüfen Sie Formel und Variablen."))
			
		return PoUOutput(latex_display=latex_display, latex_code=latex_code), codes
		
