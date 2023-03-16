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
import random

#openai.api_key = os.getenv('OPENAI_API_KEY')

# Extract fields for masking - identifier_set

def get_identifiers(sql):
    parsed_tokens = sqlparse.parse(sql)[0]
    identifier_set = set()

    reserved_words = ['TOP', 'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC']

    def process_identifier(token, identifier_set):
        identifier_name = token.get_real_name()
        if '.' in identifier_name:
            identifier_name = identifier_name.split('.')[1]
        identifier_set.add(identifier_name)

    def process_function_arguments(token, identifier_set):
        if isinstance(token, sqlparse.sql.Identifier):
            process_identifier(token, identifier_set)
        elif isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                if isinstance(identifier, sqlparse.sql.Identifier):
                    process_identifier(identifier, identifier_set)
        elif isinstance(token, sqlparse.sql.Parenthesis):
            for subtoken in token.tokens:
                process_function_arguments(subtoken, identifier_set)

    def add_identifiers_from_function(token, identifier_set):
        for subtoken in token.tokens:
            process_function_arguments(subtoken, identifier_set)

    def process_where(token, identifier_set):
        for subtoken in token.tokens:
            if isinstance(subtoken, sqlparse.sql.Comparison):
                process_identifier(subtoken.left, identifier_set)
            elif isinstance(subtoken, sqlparse.sql.Identifier):
                process_identifier(subtoken, identifier_set)

    for token in parsed_tokens.tokens:
        if isinstance(token, sqlparse.sql.Function):
            add_identifiers_from_function(token, identifier_set)
            continue
        if token.value.upper() in reserved_words:
            continue
        if isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                if isinstance(identifier, sqlparse.sql.Identifier):
                    process_identifier(identifier, identifier_set)
        elif isinstance(token, sqlparse.sql.Comparison):
            process_identifier(token.left, identifier_set)
        elif isinstance(token, sqlparse.sql.Where):
            process_where(token, identifier_set)
        elif isinstance(token, sqlparse.sql.Identifier):
            process_identifier(token, identifier_set)
    return list(identifier_set)

def sql_masking(identifiers, sql):
    """
    This function takes in a list of identifiers and an SQL query as input, and replaces the identifiers in the SQL query with random words.
    """
    # Create a dictionary to store the mapping between original identifiers and masked words
    word_map = {}
    
    # Loop through each identifier in the list of identifiers
    for identifier in identifiers:
        # Generate a random word to replace the original identifier
        random_word = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=len(identifier)))
        
        # Add the mapping to the dictionary
        word_map[identifier] = random_word
        
        # Replace the original identifier with the random word in the SQL string
        sql = re.sub(r'\b{}\b'.format(identifier), random_word, sql)
    
    # Return the masked SQL string and the word map
    return sql, word_map
 

# Open Ai piece

def sql_dialectify(to_sql, masked_sql):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": 'You are an expert SQL developer that is proficient in MS SQL Server, MySQL, Oracle, PostgreSQL, SQLite, Snowflake SQL dialects.'},
            {"role": "system", "content": 'Only return the converted sql code and do not explain the conversion process.'},
            {"role": "system", "content": 'Check for the correctness of the entered SQL code. And make updates if necessary. List the changes succinctly in the chat.'},
            {"role": "system", "content": 'Let''s think step by step.'},
            {"role": "user", "content": f'Detect the dialect of the following SQL code: "{masked_sql}"'},
            {"role": "system", "content": f'Check and fix errors for the top common SQL syntax mistakes for the detected dialect. List updated parts of the following SQL code: "{masked_sql}"'},
            {"role": "user", "content": f'Convert the updated SQL code from detected dialect to "{to_sql}": "\n\n{masked_sql}"'}
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

# TEST: Add a button to trigger the SQL dialect conversion
if openai.api_key and st.button("Extract", key="1"):
    st.write("Extracting the list of field names from your SQL Code...")

    list_of_fields = get_identifiers(sql)

    # Display the converted SQL code
    st.text_area("Extracted list of field names", list_of_fields)

# TEST: Add a button to show masked sql before it is sent to Openai
if openai.api_key and st.button("Mask", key="2"):
    st.write("Extracting the list of field names from your SQL Code...")
    
    list_of_fields = get_identifiers(sql)
    masked_sql, word_map  = sql_masking(list_of_fields, sql)

    # Display the converted SQL code
    #st.text_area("Encryted SQL", masked_sql + str(list_of_fields))
    st.text_area("Encryted SQL", masked_sql)



#from_sql = st.selectbox("From SQL:", ["MS SQL Server", "MySQL", "Oracle", "PostgreSQL", "SQLite", "Snowflake"])
to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])



# Add a button to trigger the SQL dialect conversion
if openai.api_key and st.button("Convert"):
    st.write("Converting the SQL Code...")
    # Convert the SQL dialect using the OpenAI API
    list_of_fields = get_identifiers(sql)
    masked_sql, word_map  = sql_masking(list_of_fields, sql)
    masked_converted_sql = sql_dialectify(to_sql, masked_sql)
    # Display the converted SQL code
    st.text_area("Converted SQL Code", masked_converted_sql)


# import streamlit as st
# import time

# progress_text = "Operation in progress. Please wait."
# my_bar = st.progress(0, text=progress_text)

# for percent_complete in range(100):
#     time.sleep(0.1)
#     my_bar.progress(percent_complete + 1, text=progress_text)