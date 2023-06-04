import pyodbc
import os
import openai
from dotenv import load_dotenv

FEEDBACK_QUERY = "INSERT INTO feedback (username, epoch_time, user_question, model_answer, feedback_type, comment, suggested_answer, sources) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"

class AzureSQLDatabase:
    def __init__(self, server: str = None, database : str = None, username: str = None, password : str = None, driver : str = "{ODBC Driver 18 for SQL Server}"):
        load_dotenv()
        self.server = server if server else os.getenv('SQL_SERVER')
        self.database = database if database else os.getenv('SQL_DATABASE')
        self.username = username if username else os.getenv('SQL_USERNAME')
        self.password = password if password else os.getenv('SQL_PASSWORD')
        self.driver = driver 

        return

    def get_conn(self):  
        conn = pyodbc.connect('DRIVER='+self.driver+';SERVER=tcp:'+self.server+';PORT=1433;DATABASE='+self.database+';UID='+self.username+';PWD='+ self.password)
        return conn
    
    def execute_feedback_query(self, username, epoch_time, user_question, model_answer, feedback_type, comment, suggested_answer, sources):
        with pyodbc.connect('DRIVER='+self.driver+';SERVER=tcp:'+self.server+';PORT=1433;DATABASE='+self.database+';UID='+self.username+';PWD='+ self.password) as conn:
            with conn.cursor() as cursor:
                cursor.execute(FEEDBACK_QUERY, (username, epoch_time, user_question, model_answer, feedback_type, comment, suggested_answer, sources))
        return

#with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
#    with conn.cursor() as cursor:
#        cursor.execute("SELECT TOP 3 name, collation_name FROM sys.databases")
#        row = cursor.fetchone()
#        while row:
#            print (str(row[0]) + " " + str(row[1]))
#            row = cursor.fetchone()