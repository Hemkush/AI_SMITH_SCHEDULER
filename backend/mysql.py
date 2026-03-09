import pymysql;

db_host = "database-1.co1uycuwgnxz.us-east-1.rds.amazonaws.com"
db_user = "admin"
db_name = ""
db_password = "Maryland123"

connection = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
) 
print("Database connected successfully.")      

cursor = connection.cursor()

cursor.execute("SELECT * FROM table_name")
db_version = cursor.fetchone()
print("Database version:", db_version)