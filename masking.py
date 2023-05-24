import re
import random

def sql_masking(identifiers, sql):
    """
    This function takes in a list of identifiers and an SQL query as input, 
    and replaces the identifiers in the SQL query with random words.
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