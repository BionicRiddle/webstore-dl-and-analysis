import pickle

filename = 'test.pkl'

# Pickle Object
class SaveObject:
    def __init__(self, data):
        self.data = data

# Pickle save
def save_object(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

# Pickle load
def load_object(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

o = load_object(filename).data

not_done_old = o[0]
unique_items = o[1]

# SaveObject([not_done_items, self.unique_items])


# /app/extensions/apcghpabklkjjgpfoplnglnjghonjhdl/APCGHPABKLKJJGPFOPLNGLNJGHONJHDL_1_17_0_0.crx


list_of_id = []
for i in unique_items:
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

for i in not_done:
    ext_path = './extensions/' + i
    #get files in directory

    for root, dirs, files in os.walk(ext_path):
        for file in files:
            if file.endswith(".crx"):
                path_list.append(os.path.join(ext_path, file))
                break

s = SaveObject([path_list, unique_items])

filename_save = 'out.pkl'
save_object(s, filename_save)

print('done')

print(len(path_list))
print(len(unique_items))