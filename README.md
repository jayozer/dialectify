# dialectify
Convert SQL code from one dialect to another using ChatGPT API and Streamlit


to do:
- Use your own API_KEY for ChatGPT API.
- Check for any issues/ validate code for the given dialect. Maybe detect dialect should be removed to catch validation mistakes
- Encode / decode before sending to openai to mask any business non public info (fields and table names)
- Toggles for replace any char (such as #) with any char (such as _)
- Add _VIEW and capitalize table names only. Field names should be lower case
- It corrects syntax errors, not needed! Only for specific use case
- Toggle to replace any char with another one. This is to update # to _
SELECT C.RootId#, C.Id#,
     FROM pfm.Contact AS C WITH (NOLOCK)

- Ability to add _ between words in field names (tricky) - Tokenize meaningful parts of a field name and seprate it using _
