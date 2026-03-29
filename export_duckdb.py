import duckdb

con = duckdb.connect("data/processed/flights.duckdb", read_only=True)

print(con.execute("SHOW TABLES").fetchall())

con.execute("""
COPY flights TO 'flights_export.csv' (HEADER, DELIMITER ',');
""")

