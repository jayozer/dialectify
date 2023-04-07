import sqlparse
import streamlit as st

def parse_tables_views(query):
    parsed_query = sqlparse.parse(query)[0]
    tables = []
    views = []
    for token in parsed_query.tokens:
        if isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                if "." in identifier.value:
                    table_or_view = identifier.value.split(".")[0]
                    if table_or_view not in tables and table_or_view not in views:
                        if "TABLE" in identifier.parent.value.upper():
                            tables.append(table_or_view)
                        elif "VIEW" in identifier.parent.value.upper():
                            views.append(table_or_view)
    return tables, views

def main():
    st.title("SQL Parser")

    query = st.text_area("Enter SQL Query")
    if st.button("Parse"):
        tables, views = parse_tables_views(query)
        st.write("Tables: ", tables)
        st.write("Views: ", views)

if __name__ == '__main__':
    main()
