from blazingsql import BlazingContext

# Start up BlazingSQL
bc = BlazingContext()

# Create table from CSV
bc.create_table('taxi', '/blazingdb/data/mockup.csv')

# Query table (Results return as cuDF DataFrame)
gdf = bc.sql('SELECT * FROM mockup')

# Display query results 
print(gdf)