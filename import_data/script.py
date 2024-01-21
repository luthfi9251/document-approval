from erppeek import Client
import pandas as pandas

USERNAME = "admin"
PASSWORD = "admin"
DB = "doc-approval"
SERVER = "http://localhost:8069"

client = Client(SERVER, db=DB, user=USERNAME, password=PASSWORD)
users = client.search('res.users', [])

print(users)