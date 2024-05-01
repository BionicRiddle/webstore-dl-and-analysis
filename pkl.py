import pickle

filename = 'test.pkl'

# Pickle Object
class SaveObject:
    def __init__(self, data):
        self.data = data

def load_data(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    
    return data

o = load_data(filename)

# /app/extensions/apcghpabklkjjgpfoplnglnjghonjhdl/APCGHPABKLKJJGPFOPLNGLNJGHONJHDL_1_17_0_0.crx
list_of_ext = o.data[1]


list_of_id = []
for i in list_of_ext:
    list_of_id.append(i.split('/')[3])


#load sqlite db thesis.db
import sqlite3

conn = sqlite3.connect('thesis.db')
c = conn.cursor()

#query "domain" table columen unique extension
c.execute("SELECT DISTINCT extension FROM domain")

#fetch all rows
rows = c.fetchall()
print(len(rows))

not_done = []

for id in list_of_id:
    if (id,) not in rows:
        not_done.append(id)
    
print(len(not_done))

# get full path of extension file

path_list = []
import os

for i in list_of_ext:
    ext_path = './extensions/' + i
    #get files in directory

    for root, dirs, files in os.walk(ext_path):
        for file in files:
            if file.endswith(".crx"):
                path_list.append(os.path.join(ext_path, file))
                print(os.path.join(ext_path, file))
                break

print(len(path_list))