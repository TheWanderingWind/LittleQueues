from pymongo import MongoClient

# Підключення до MongoDB сервера
client = MongoClient('mongodb://localhost:27017/')

# Вибір бази даних
db = client['QueuesData']

# Вибір колекції
collection = db['queues']

# Виконання запиту на вибірку даних
result = collection.find()

# Виведення результатів
for document in result:
    print(document)

# Закриття з'єднання
client.close()
