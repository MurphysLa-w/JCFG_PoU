# Entry Level Page Manager

__version__ = "2.0.2-beta"

import streamlit as st

pg = st.navigation([st.Page("pages/jcfg_calculator.py", title="Rechner"), st.Page("pages/jcfg_tutorial.py", title="Tutorial", visibility="hidden")])
pg.run()

