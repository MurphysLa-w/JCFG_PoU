import pandas as pd
import streamlit as st

# Initial scorecard dataframe
scorecard = pd.DataFrame(columns=['User', 'Pushups', 'Pullups', 'Totaled'])

# Input your data using experimental data editor
st.write("Input your data below:")
input_data = pd.DataFrame(index=[0], columns=['User', 'Pushups', 'Pullups'])
input_data = input_data.fillna(0)  # fill with zeros

edited_data = st.experimental_data_editor(input_data)

# Handle user input
if st.button('Submit'):
    edited_data['Totaled'] = edited_data['Pushups'] + edited_data['Pullups']
    scorecard = scorecard.append(edited_data, ignore_index=True)

# Display the updated scorecard
st.write("Updated Scorecard:")
st.table(scorecard)
