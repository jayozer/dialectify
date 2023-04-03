
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

# Demask Converted SQL
def demasking(word_map, masked_sql):
    """
    This function takes in a word map and a masked SQL string as input and replaces the masked words with their original words.
    """
    # Loop through each key-value pair in the word map
    for original_word, masked_word in word_map.items():
        # Replace the masked word with the original word in the SQL string
        sql_string = re.sub(r'\b{}\b'.format(masked_word), original_word, masked_sql)
    
    # Return the demasked SQL string
    return sql_string

# Extract tables to append _view

def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, Identifier):
            yield item.get_real_name()
        elif isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                yield identifier.get_real_name()
        elif item.ttype is Name:
            yield item.value


def extract_tables(sql):
    parsed = sqlparse.parse(sql)[0]
    token_stream = extract_table_identifiers(parsed.tokens)
    table_set = set()
    
    for token in token_stream:
        if token.upper() != "AS":
            table_set.add(token)

    return list(table_set)


def append_view_to_tables(sql, tables, add_view_suffix):
    updated_sql = sql
    if add_view_suffix:
        for table in tables:
            updated_sql = updated_sql.replace(table, f"{table}_view")
    return updated_sql

# Define Streamlit app
def app():
    # Set the app title
    st.title("Dialectify SQL")

    # Create the input boxes for the SQL code and the SQL dialects
    openai.api_key = st.text_input("Enter API Key:")
    sql = st.text_area("Enter SQL Code")
    to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])


    # Add _view
    add_view_suffix = st.checkbox("Append '_view' to table names")

    # Extract list of field names from SQL code
    if st.button("Extract"):
        st.write("Extracting the list of field names from your SQL Code...")
        list_of_fields = get_identifiers(sql)
        st.text_area("Extracted list of field names", list_of_fields)

    # Mask SQL code
    if st.button("Mask"):
        st.write("Masking your SQL Code...")
        list_of_fields = get_identifiers(sql)
        masked_sql, word_map = sql_masking(list_of_fields, sql)
        st.text_area("Encrypted SQL", masked_sql)

    # Convert SQL dialect
    if st.button("Convert"):
        st.write("Converting your SQL Code...")
        list_of_fields = get_identifiers(sql)
        masked_sql, word_map = sql_masking(list_of_fields, sql)
        masked_converted_sql = sql_dialectify(to_sql, masked_sql)
        st.text_area("Converted SQL Code", masked_converted_sql)

    # Demask SQL code
    if st.button("DeMask"):
        st.write("Demasking your SQL Code...")
        list_of_fields = get_identifiers(sql)
        masked_sql, word_map = sql_masking(list_of_fields, sql)
        masked_converted_sql = sql_dialectify(to_sql, masked_sql)
        demasked_sql = demasking(word_map, masked_converted_sql)
        st.code("Decrypted SQL", demasked_sql)

    # Process SQL code
    if st.button("Process SQL"):
        st.write("Processing your SQL Code...")
        list_of_fields = get_identifiers(sql)
        masked_sql, word_map = sql_masking(list_of_fields, sql)
        masked_converted_sql = sql_dialectify(to_sql, masked_sql)
        demasked_sql = demasking(word_map, masked_converted_sql)
        tables = extract_tables(sql)
        updated_sql = append_view_to_tables(demasked_sql, tables, add_view_suffix)
        st.subheader("Original SQL:")
        st.code(sql)
        st.subheader("Updated SQL:")
        st.code(updated_sql)
        
# st.title("Dialectify SQL")
# openai.api_key = st.text_input("Enter API Key:")
# sql = st.text_area("Enter SQL Code")

# if st.button("Extract", key="1"):
#     st.write("Extracting the list of field names from your SQL Code...")

#     list_of_fields = get_identifiers(sql)

#     st.text_area("Extracted list of field names", list_of_fields)

# if st.button("Mask", key="2"):
#     st.write("Extracting the list of field names from your SQL Code...")
#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)

#     st.text_area("Encrypted SQL", masked_sql)

# to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])

# if st.button("Convert"):
#     st.write("Converting the SQL Code...")

#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)

#     st.text_area("Converted SQL Code", masked_converted_sql)

# if st.button("DeMask", key="5"):
#     st.write("De mAsking for further processing SQL Code...")
    
#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)
#     demasked_sql = demasking(word_map, masked_converted_sql)

#     st.code("Demasked SQL", demasked_sql)

# add_view_suffix = st.checkbox("Append '_view' to table names")



# #-----------Above works, below does not.
# if st.button("Process SQL",  key="3"): 

#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)
#     demasked_sql = demasking(word_map, masked_converted_sql)

#     tables = extract_tables(demasked_sql)
#     updated_sql = append_view_to_tables(sql, tables, add_view_suffix)

    

#     st.subheader("Original SQL:")
#     st.code(sql)

#     st.subheader("Updated SQL:")
#     st.code(updated_sql)

# # Define the Streamlit app using the st package:

# # Set the app title
# st.title("Dialectify SQL")

# # Create the input boxes for the SQL code and the SQL dialects
# openai.api_key = st.text_input("Enter API Key:")
# sql = st.text_area("Enter SQL Code")

# # TEST: Add a button to trigger the SQL dialect conversion
# if openai.api_key and st.button("Extract", key="1"):
#     st.write("Extracting the list of field names from your SQL Code...")

#     list_of_fields = get_identifiers(sql)

#     # Display the converted SQL code
#     st.text_area("Extracted list of field names", list_of_fields)

# # TEST: Add a button to show masked sql before it is sent to Openai
# if openai.api_key and st.button("Mask", key="2"):
#     st.write("Extracting the list of field names from your SQL Code...")
    
#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)

#     # Display the converted SQL code
#     #st.text_area("Encryted SQL", masked_sql + str(list_of_fields))
#     st.text_area("Encrypted SQL", masked_sql)



# #from_sql = st.selectbox("From SQL:", ["MS SQL Server", "MySQL", "Oracle", "PostgreSQL", "SQLite", "Snowflake"])
# to_sql = st.selectbox("To SQL:", ["MS SQL Server", "MySQL", "Oracle Database", "PostgreSQL", "SQLite", "Snowflake"])



# # Add a button to trigger the SQL dialect conversion
# if openai.api_key and st.button("Convert"):
#     st.write("Converting the SQL Code...")
#     # Convert the SQL dialect using the OpenAI API
#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)
#     # Display the converted SQL code
#     st.text_area("Converted SQL Code", masked_converted_sql)




# if openai.api_key and st.button("DeMask", key="5"):
#     st.write("De mAsking for further processing SQL Code...")
    
#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     word_map_decode  = word_map

#      # Dialectify
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)

#     # Demask the SQL string
#     demasked_sql = demasking(word_map_decode, masked_converted_sql)

#     # Print the demasked SQL string
#     st.code("Encrypted SQL", demasked_sql)


# # import streamlit as st
# # import time

# # progress_text = "Operation in progress. Please wait."
# # my_bar = st.progress(0, text=progress_text)

# # for percent_complete in range(100):
# #     time.sleep(0.1)
# #     my_bar.progress(percent_complete + 1, text=progress_text)



# # Add _view


# # tables = extract_tables(sql)
# # updated_sql = append_view_to_tables(sql, tables, add_view_suffix)

# # st.write('Updated SQL:\n', updated_sql)

# if st.button("Process SQL",  key="3"): 

#     list_of_fields = get_identifiers(sql)
#     masked_sql, word_map  = sql_masking(list_of_fields, sql)
#     word_map_decode  = word_map

#      # Dialectify
#     masked_converted_sql = sql_dialectify(to_sql, masked_sql)

#     # Demask the SQL string
#     demasked_sql = demasking(word_map_decode, masked_converted_sql)

#     # Print the demasked SQL string
#     tables = extract_tables(sql)
#     updated_sql = append_view_to_tables(demasked_sql, tables, add_view_suffix)

#     st.subheader("Original SQL:")
#     st.code(sql)

#     st.subheader("Updated SQL:")
#     st.code(updated_sql)