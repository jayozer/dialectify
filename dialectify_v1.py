import re
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

# Extract fields for masking - identifier_set

def get_identifiers(sql):
    parsed_tokens = sqlparse.parse(sql)[0]
    identifier_set = set()

    reserved_words = ['TOP', 'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC']

    def process_identifier(token, identifier_set):
        # Get the real name of the token
        identifier_name = token.get_real_name()
        # If the real name contains a dot, split it on the dot and take the second part
        if '.' in identifier_name:
            identifier_name = identifier_name.split('.')[1]
        # Add the identifier name to the set
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
# Create a sidebar in Streamlit
st.sidebar.title("Dialectify SQL")

# Add a selectbox for max_tokens to the sidebar with a text box
# User can enter the integer value of max_tokens and select it from the dropdown.
# Also add a note to the sidebar explaining the purpose of max_tokens.
max_tokens = st.sidebar.selectbox("Enter Max Tokens", [1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192], index=0) 
st.sidebar.markdown("GPT-4 has a maximum token limit of 8,192 tokens (equivalent to ~6000 words), whereas GPT-3.5's 4,000 tokens (equivalent to 3,125 words)")

# model_choice = st.sidebar.selectbox("Model:", ["gpt-3.5-turbo", "gpt-4"])
model_choice = st.sidebar.radio("Model:", ["gpt-3.5-turbo", "gpt-4"])
temperature = st.sidebar.selectbox("Temperature:", [0.1, 0.2, 0.3, 0.9], index=1)

def sql_dialectify(from_sql, to_sql, original_sql, max_tokens=max_tokens, model_choice=model_choice, temperature=temperature, mask_fields=False, identifiers=None):
    # If mask_fields is True, mask the fields using the provided sql_masking function
    if mask_fields and identifiers:
        masked_sql, word_map = sql_masking(identifiers, original_sql)
    else:
        masked_sql = original_sql

    completion = openai.ChatCompletion.create(
        model=model_choice,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
           {"role": "system", "content": 'Act as CODEX ("COding DEsign eXpert"), an expert coder with proficiency in SQL programming language.'},
            {"role": "system", "content": 'You are proficient in Transact-SQL, MySQL, PL/SQL, PL/pgSQL, SQLite, and Snowflake SQL dialects, with a focus on high accuracy dialect to dialect conversions.'},
            {"role": "system", "content": 'Your task is to convert a specific SQL script from one SQL dialect to another SQL dialect while maintaining the functionality and integrity of the original script.'},
            {"role": "system", "content": f'The source SQL dialect is "{from_sql}", and the target SQL dialect is "{to_sql}". Your goal is to perform a precise SQL dialect conversion while addressing any incompatibilities or differences.'},
            {"role": "system", "content": 'Always follow the coding best practices by writing clean, modular code with proper security measures and leveraging design patterns.'},
            {"role": "system", "content": f'You will identify and address differences in data types and functions between the {from_sql} and {to_sql} dialects. For data types or functions without a direct equivalent, choose the most suitable alternative'},
            {"role": "system", "content": 'You will return your answers in two sections. In the first section you will return the converted sql query in a code block. You will title this section as "\n ### Converted SQL: ".'},
            {"role": "system", "content": 'In the second section you will return Any comments and the explanations of the changes with bulled points. You will title this section as "### Conversion details: ".'},
            {"role": "user", "content": f'Convert the following SQL code from "{from_sql}" to "{to_sql}" while ensuring the highest level of accuracy in maintaining the original functionality: "\n\n{masked_sql}"'},
        
        ]
    )

    converted_sql = completion.choices[0].message.content

    # If mask_fields is True, replace the masked words with the original identifiers
    if mask_fields and identifiers:
        for original, masked in word_map.items():
            converted_sql = converted_sql.replace(masked, original)

    return converted_sql

# # Demask Converted SQL
# def demasking(word_map, masked_sql):
#     """
#     This function takes in a word map and a masked SQL string as input and replaces the masked words with their original words.
#     """
#     demasked_sql = masked_sql

#     # Loop through each key-value pair in the word map
#     for original_word, masked_word in word_map.items():
#         # Replace the masked word with the original word in the SQL string
#         demasked_sql = re.sub(r'\b{}\b'.format(masked_word), original_word, demasked_sql)
    
#     # Return the demasked SQL string
#     return demasked_sql

# get the list of tables in a query
def tables_in_query(sql_str):

    # remove the /* */ comments
    q = re.sub(r"/\*[^*]*\*+(?:[^*/][^*]*\*+)*/", "", sql_str)

    # remove whole line -- and # comments
    lines = [line for line in q.splitlines() if not re.match("^\s*(--|#)", line)]

    # remove trailing -- and # comments
    q = " ".join([re.split("--|#", line)[0] for line in lines])

    # split on blanks, parens and semicolons
    tokens = re.split(r"[\s)(;]+", q)

    # scan the tokens. if we see a FROM or JOIN, we set the get_next
    # flag, and grab the next one (unless it's SELECT).

    result = set()
    get_next = False
    for tok in tokens:
        if get_next:
            if tok.lower() not in ["", "select"]:
                result.add(tok)
            get_next = False
        get_next = tok.lower() in ["from", "join"]

    return result

# Extract tables for db views
if st.button("Extract tables", use_container_width=True):
    # Extract tables from SQL code
    st.write(f"Here are the table name. Check if the view definitions already exist in the db...")
    tables = tables_in_query(sql)

    # Display tables
    st.code(tables)

# From and To sql dialect choices
from_sql = st.selectbox("From SQL:", ["Transact-SQL", "MySQL", "PL/SQL", "PL/pgSQL", "SQLite", "Snowflake"])
to_sql = st.selectbox("To SQL:", ["Transact-SQL", "MySQL", "PL/SQL", "PL/pgSQL", "SQLite", "Snowflake"])

#mask fields or not
mask_fields = st.checkbox("Mask all fields including table/view names before sending the query to OpenAI")
# Append _view to table names
add_view_suffix = st.checkbox ("Append '_view' to table names after the conversion")

if st.button("Dialectify"):
    st.write(f"Converting your SQL Code from {from_sql} to {to_sql}...")
    converted_sql = sql_dialectify(from_sql, to_sql, sql, max_tokens, model_choice, temperature, mask_fields)
    st.subheader("Updated SQL:")
    formatted_sql = sqlparse.format(converted_sql, reindent=True, keyword_case='upper')
    if add_view_suffix:
        tables = tables_in_query(formatted_sql)
        for table in tables:
            formatted_sql = formatted_sql.replace(table, f"{table}_view")
    st.code(formatted_sql, language="sql")
    st.write(f'Your SQL code is converted from {from_sql} to {to_sql}. Validate the output!')
    