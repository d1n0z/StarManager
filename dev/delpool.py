import pickle

with open('pool.p', 'rb') as file:
    pool = pickle.load(file)
    file.close()
pool.pop('746110579')  # [uids]
pool.pop('697163236')  # [uids]
with open('pool.p', 'wb') as data:
    pickle.dump(pool, data, protocol=pickle.HIGHEST_PROTOCOL)
    data.close()
print('created: "blacklist.p"')
