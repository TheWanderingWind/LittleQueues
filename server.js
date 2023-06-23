const mongodb = require('mongodb');
const MongoClient = mongodb.MongoClient;

const url = 'mongodb://localhost:27017';
const dbName = 'QueuesData';

// Функція для додавання нового екземпляру черги
function addQueue(queueData, callback) {
  MongoClient.connect(url, (err, client) => {
    if (err) {
      console.error('Помилка підключення до MongoDB:', err);
      return;
    }
  
    const db = client.db(dbName);
    const queuesCollection = db.collection('queues');
  
    // Створення нового екземпляру черги
    const newQueue = {
      id: queueData.id,
      ownerId: queueData.ownerId,
      name: queueData.name,
      description: queueData.description,
      queue: [],
      finishedQueue: [],
      status: 'active'
    };
  
    queuesCollection.insertOne(newQueue, (err, result) => {
      if (err) {
        console.error('Помилка при додаванні нової черги:', err);
        callback(err, null);
      } else {
        console.log('Нова черга була додана');
        callback(null, result);
      }
      client.close();
    });
  });
}

// Функція для додавання нового учасника
function addUser(userData, callback) {
  MongoClient.connect(url, (err, client) => {
    if (err) {
      console.error('Помилка підключення до MongoDB:', err);
      return;
    }
  
    const db = client.db(dbName);
    const usersCollection = db.collection('users');
  
    // Створення нового учасника
    const newUser = {
      id: userData.id,
      name: userData.name,
      cookie: userData.cookie
    };
  
    usersCollection.insertOne(newUser, (err, result) => {
      if (err) {
        console.error('Помилка при додаванні нового учасника:', err);
        callback(err, null);
      } else {
        console.log('Новий учасник був доданий');
        callback(null, result);
      }
      client.close();
    });
  });
}

// Приклад використання функцій
const queueData = {
  id: 1,
  ownerId: 1,
  name: 'Queue 1',
  description: 'This is queue 1'
};

const userData = {
  id: 1,
  name: 'User 1',
  cookie: 'user1cookie'
};

addQueue(queueData, (err, result) => {
  if (err) {
    console.error('Помилка при додаванні черги:', err);
  } else {
    console.log('Черга була успішно додана');
  }
});

addUser(userData, (err, result) => {
  if (err) {
    console.error('Помилка при додаванні учасника:', err);
  } else {
    console.log('Учасник був успішно доданий');
  }
});
