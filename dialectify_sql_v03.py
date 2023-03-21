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
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML, Name

import time

#openai.api_key = os.getenv('OPENAI_API_KEY')

# Declare word_map and masked_converted_sql as global variables
word_map = {}
masked_converted_sql = ""


# Set the app title
st.title("Dialectify SQL")

# Create the input boxes for the SQL code and the SQL dialects
openai.api_key = st.text_input("Enter API Key:")
sql = st.text_area("Enter SQL Code")
to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])

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
        model="gpt-4",
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

# Demask Converted SQL
def demasking(word_map, masked_sql):
    """
    This function takes in a word map and a masked SQL string as input and replaces the masked words with their original words.
    """
    demasked_sql = masked_sql

    # Loop through each key-value pair in the word map
    for original_word, masked_word in word_map.items():
        # Replace the masked word with the original word in the SQL string
        demasked_sql = re.sub(r'\b{}\b'.format(masked_word), original_word, demasked_sql)
    
    # Return the demasked SQL string
    return demasked_sql

# Extract tables to append _view

def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, Identifier):
            yield item.get_real_name()
        elif isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                if isinstance(identifier, Identifier):
                    yield identifier.get_real_name()


def append_view_to_tables(sql, tables, add_view_suffix=False):
    updated_sql = sql
    for table in tables:
        if add_view_suffix:
            updated_sql = updated_sql.replace(table, f"{table}_view")
        else:
            updated_sql = updated_sql.replace(f"{table}_view", table)
    return updated_sql


def extract_tables(sql):
    parsed = sqlparse.parse(sql)[0]
    token_stream = extract_table_identifiers(parsed.tokens)
    table_set = set()

    for token in token_stream:
        if token != "AS":
            table_set.add(token)

    return list(table_set)

 
# Append _view
add_view_suffix = st.checkbox("Append '_view' to table names")


# Convert SQL dialect
if st.button("Mask"):
    st.write("Encrpyting your SQL Code...")
    list_of_fields = get_identifiers(sql)
    masked_sql, word_map = sql_masking(list_of_fields, sql)
    st.code(masked_sql)

if st.button("Dialectify"):
    st.write(f"Converting your SQL Code to {to_sql}...")
    list_of_fields = get_identifiers(sql)
    masked_sql, word_map = sql_masking(list_of_fields, sql)
    masked_converted_sql = sql_dialectify(to_sql, masked_sql)

    demasked_sql = demasking(word_map, masked_converted_sql)

    tables = extract_tables(demasked_sql)
   
    updated_sql = append_view_to_tables(demasked_sql, tables, add_view_suffix)
    
    st.subheader("Original SQL:")
    st.code(sql)
    st.subheader("Updated SQL:")
    st.code(updated_sql)



