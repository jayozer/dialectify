# I want you to act like a python developer and build me a Streamlit app for the above functionality. 
# You will use Python and Streamlit libraries. The app accepts sql code as an input from the user. 
# Under the sql input box, there are two pickers. One is named "From SQL:" and the other is named as "To SQL:"  Both take user input.
# Once all fields are entered, the app converts the user inputted SQL Dialect to the new requested dialect in the "From SQL:" picker. 
# To convert the sql dialect the app must use OpenAI ChatGPT API, the model name: gpt-3.5-turbo

# The app must be deployed with streamlit share.
import re
import requests
import os
import streamlit as st
import openai
from dotenv import load_dotenv
# loads .env file located in the current directory
load_dotenv() 

openai.api_key = os.getenv('OPENAI_API_KEY')

# Open Ai piece

def sql_dialectify(to_sql, sql):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": 'You are an expert SQL developer that is proficient in MS SQL Server, MySQL, Oracle, PostgreSQL, SQLite, Snowflake SQL dialects.'},
            {"role": "system", "content": 'Only return the converted sql code and do not explain the conversion process.'},
            {"role": "system", "content": 'Check for the correctness of the entered SQL code. And make updates if necessary. List the changes succinctly in the chat.'},
            {"role": "system", "content": 'Check and fix for top fifteen common SQL syntax mistakes that can lead to errors or incorrect results in SQL statements.'},
            {"role": "system", "content": 'Let''s think step by step.'},
            {"role": "user", "content": f'Detect the dialect of the following SQL code: "{sql}"'},
            {"role": "user", "content": f'Convert the following SQL code from detected dialect to {to_sql}: "\n\n{sql}"'}
        ]
    )
    converted_sql = completion.choices[0].message.content
    return converted_sql


# Define the Streamlit app using the st package:

# Set the app title
st.title("SQL Dialect Converter")

# Create the input boxes for the SQL code and the SQL dialects
sql = st.text_area("Enter SQL Code")
#from_sql = st.selectbox("From SQL:", ["MS SQL Server", "MySQL", "Oracle", "PostgreSQL", "SQLite", "Snowflake"])
to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])

# Add a button to trigger the SQL dialect conversion
if st.button("Convert"):
    # Convert the SQL dialect using the OpenAI API
    converted_sql = sql_dialectify(to_sql, sql)
    # Display the converted SQL code
    st.text_area("Converted SQL Code", converted_sql)


