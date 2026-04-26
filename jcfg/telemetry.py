# Functions to gather data and feedback

import datetime
import requests
import streamlit as st
from .exit_codes import ExitCode

bug_report_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSeVAsZtEX3mRK8sPX_FiMO2mYMY2CVXj8nm41YOtwZyEcbuSg/formResponse"
telemetry_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSd17V0q-9yM1DKa7cpxGGiRbi-NnSL2VNcdH4RPE8tcxSDh4Q/formResponse"

def submit_bug_report(bug_kind, bug_desc, bug_email, current_state):
	codes = []
	bug_report = {
		"entry.320798035"	: bug_kind,
		"entry.1002995150"	: bug_desc,
		"entry.519864065"	: bug_email,
		"entry.74602100"	: str(current_state)
		}
	
	# Posting it to the form
	res = requests.post(bug_report_url, data=bug_report)
	
	# Check sucess
	if res.status_code == 200 and bug_email != "":
		codes.append(ExitCode(333))
	elif res.status_code == 200:
		codes.append(ExitCode(332))
	else:
		codes.append(ExitCode(134))
	return codes

def log(eq):
	now = datetime.datetime.now(datetime.UTC)
	if eq!=r"\rho_\text{Wasser} = \frac{m_\text{Wasser}}{V_\text{Wasser}}" and "log" not in st.session_state:
		st.session_state.log = now
		requests.post(telemetry_url, data={"entry.99200264": now.strftime("%m%d%H"), "entry.1358837103":eq, "entry.644797731":"Load_Ping"})
	elif eq!=r"\rho_\text{Wasser} = \frac{m_\text{Wasser}}{V_\text{Wasser}}" and (now-st.session_state.log).total_seconds() > 300:
		st.session_state.log = now
		requests.post(telemetry_url, data={"entry.99200264": now.strftime("%m%d%H"), "entry.1358837103":eq, "entry.644797731":"Rerun_Ping"})
