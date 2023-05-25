# [dialectify](https://dialectifysql.streamlit.app/)

Convert SQL code from one dialect to another using ChatGPT API and Streamlit


V1.0:
+ Use your own API_KEY for ChatGPT API.
+ Streamlit app, incl repo updates.
+ Check for any issues/ validate code for the given dialect. Maybe detect dialect should be removed to catch validation mistakes
+ Encode / decode before sending to openai to mask any business non public info (fields and table names)
+ Add _VIEW and capitalize table names only. Field names should be lower case
+ Add Sidebar with model, token size and temperature settings

V1.1:
+ Update sidebar to have model choice first and rest of the drop down updates according to first linked choice
+ Add max token per model - users are not even familiar with token concept. (Removed max token entirely, not user intuitive)
- Update Name: SQL Dialect Switcher
- Add description: Dialectify is an app that can convert a dialect of one SQL script to another. It can also mask the field and table names and even add _view to table names for warehousing. This makes it easy to use SQL scripts on different platforms and to protect sensitive data.
- Update masking for tables and views.
+ Add copy feature to only the code
+ Display the changes to the query after the query in a bulleted list



Won't do for now
- Toggle to replace any char any char (such as #) with any char (such as _) (SELECT C.RootId#, C.Id# FROM pfm.Contact AS C WITH (NOLOCK))
- Ability to add _ between words in field names (tricky) - Tokenize meaningful parts of a field name and seperate it using _
