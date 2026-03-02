# Utils and dataclasses

import streamlit as st
from dataclasses import dataclass

@dataclass
class ExitCode:
	code: int	# Codes: 100 warn, 200 error, else info
	value: str	# Message value

'''
Code Naming:
0yz DEBUG
1yz	WARNING
2yz ERROR
3yz SUCCESS
4yz INFO

x0z Input
x1z Refining
x2z Calculation
x3z Program

All Codes:
200 General Error
201 "=" missing
202 >26
203 ==0
204 all const
205 len short		also 105
206 not in eq
207 in blacklist

210 Formula Error
211 dx Tuple
212 unkn symbol
213 (ln)

220 Calc Error
121 missing value
122 Tree
123 infinty

230 Program Error
231 Import fehlgeschlagen
332 submitted
333 submitted with reply
134	Bug failed
'''

def display_ExitCodes(codes, DEBUG):
	critical = False
	for excode in codes:
		if excode.code // 100 == 0:
			if DEBUG:
				st.info(excode.value)
		elif excode.code // 100 == 1:
			if DEBUG:
				st.warning(excode.value + "\n\n ExitCode: " + str(excode.code), icon="⚠️")
			else:
				st.warning(excode.value, icon="⚠️")
		elif excode.code // 100 == 2:
			if DEBUG:
				st.error(excode.value + "\n\n ExitCode: " + str(excode.code), icon="🚨")
			else:
				st.error(excode.value, icon="🚨")
			critical = True
		elif excode.code // 100 == 3:
			if DEBUG:
				st.success(excode.value + "\n\n ExitCode: " + str(excode.code), icon="✅️")
			else:
				st.success(excode.value, icon="✅️")
		else:
			if DEBUG:
				st.info(excode.value + "\n\n ExitCode: " + str(excode.code), icon="❕️")
			else:
				st.info(excode.value, icon="❕️")
	if critical:
		st.error("Korrigieren Sie zuerst die Fehler in der Formel und der Tabelle", icon="🚨")
	
	return critical

def to_float_safe(value):
	if value is None:
		return None
	
	if isinstance(value, float):
		return value
	
	if isinstance(value, int):
		return float(value)
	
	if isinstance(value, str):
		value = value.strip().replace(",", ".")
		try:
			return float(value)
		except ValueError:
			return None
	
	return None

def to_str_safe(value):
	if value is None:
		return "nan"
	
	elif isinstance(value, str):
		if value.lower() in ("nan", ""):
			return "nan"
		else:
			return str(value)
	
	else:
		try:
			spl = str(value).split("e")
			res = spl[0] + " \\cdot 10^{" + spl[1] + "}"
			return res
		except:
			return str(value)
	



