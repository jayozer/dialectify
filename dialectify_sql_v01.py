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

import sqlparse

#openai.api_key = os.getenv('OPENAI_API_KEY')

# Extract fields for masking
# Return fields from the sql for encoding, pick up where clause only
def get_where_fields(sql):
    parsed_query = sqlparse.parse(sql)[0]
    where_clause = None
    for token in parsed_query.tokens:
        if isinstance(token, sqlparse.sql.Where):
            where_clause = token
            break
    if not where_clause:
        return []
    fields = []
    for token in where_clause.tokens:
        if isinstance(token, sqlparse.sql.Comparison):
            left = token.left
            if isinstance(left, sqlparse.sql.Identifier):
                fields.append(left.get_name())
            elif isinstance(left, sqlparse.sql.Function):
                fields.append(left.tokens[0].get_name())
    return fields

# Works for identifiers that are select columns and table names
def get_identifiers(sql):
    parsed_tokens = sqlparse.parse(sql)[0]
    identifier_set = set()
    for token in parsed_tokens:
        if isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                identifier_name = identifier.get_name()
                if '.' in identifier_name:
                    identifier_name = identifier_name.split('.')[1]
                identifier_set.add(identifier_name)
        elif isinstance(token, sqlparse.sql.Identifier):
            identifier_name = token.get_name()
            if '.' in identifier_name:
                identifier_name = identifier_name.split('.')[1]
            identifier_set.add(identifier_name)
    return list(identifier_set)


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
st.title("Dialectify SQL")

# Create the input boxes for the SQL code and the SQL dialects
openai.api_key = st.text_input("Enter API Key:")
sql = st.text_area("Enter SQL Code")

# Add a button to trigger the SQL dialect conversion
if openai.api_key and st.button("Extract"):
    st.write("Extracting the list of field names from your SQL Code...")

    identifiers = get_identifiers(sql)
    where_fields = get_where_fields(sql)
    list_of_fields = identifiers + where_fields
    # Display the converted SQL code
    st.text_area("Extracted list of field names", list_of_fields)


#from_sql = st.selectbox("From SQL:", ["MS SQL Server", "MySQL", "Oracle", "PostgreSQL", "SQLite", "Snowflake"])
to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])



# Add a button to trigger the SQL dialect conversion
if openai.api_key and st.button("Convert"):
    st.write("Converting the SQL Code...")
    # Convert the SQL dialect using the OpenAI API
    converted_sql = sql_dialectify(to_sql, sql)
    # Display the converted SQL code
    st.text_area("Converted SQL Code", converted_sql)


