
import streamlit as st

st.title("Hello World")
st.text("Hi I a text")
formIn = st.text_input("Enter Formula here", r"i.e. \frac{m}{V}")
print(formIn)
st.text(formIn)
