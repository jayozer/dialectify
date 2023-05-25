# [dialectify](https://dialectifysql.streamlit.app/)

Convert SQL code from one SQL dialect to another using ChatGPT API and Streamlit. 
<br> Dialectify is an app that can convert a dialect of one SQL script to another. It can also mask the field and table names and also can add **_view** to table names for warehousing. This makes it easy to use SQL scripts on different platforms and not share sensitive data.

- Use your own API_KEY for ChatGPT API.
- Check for any issues/ validate code for the given dialect. Provide the input sql dialect.
- Encode / decode before sending to openai to mask any business non public info (fields and table names)
- Add _VIEW and capitalize table names only. Field names should be lower case
- Add Sidebar with model, info and temperature settings

