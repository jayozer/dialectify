# dialectify
Convert SQL code from one dialect to another using ChatGPT API and Streamlit


to do:
- Use your own API_KEY for Codex.
- Encode / decode before sending to openai to mask any business non public info (fields and table names)
- Replace any char with another one. This is to update # to _
SELECT C.RootId#, C.Id#,
     FROM pfm.Contact AS C WITH (NOLOCK)

- Ability to add _ between words in field names (tricky)
