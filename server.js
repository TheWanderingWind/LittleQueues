///////// includes //////////////////////
const express = require('express');
const cookieParser = require('cookie-parser');
const app = express();

const mongodb = require('mongodb');
const MongoClient = mongodb.MongoClient;

const url = 'mongodb://localhost:27017';
const dbName = 'QueuesData';

app.use(cookieParser());
let db;


///////// data functions //////////////////////
MongoClient.connect(url, (err, client) => {
  if (err) {
    console.error('Помилка підключення до MongoDB:', err);
    return;
  }
  
  db = client.db(dbName);
  console.log('Підключено до MongoDB');
});


// Function for add new queue
function addQueue(queueData, callback) {
    const queuesCollection = db.collection('queues');
  
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
}


// Function for add new client
function addUser(userData, callback) {

    const usersCollection = db.collection('users');
  
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
}


///////// test data //////////////////////
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


///////// setup server //////////////////////
app.listen(3000, () => {
  console.log('Сервер запущений на порту 3000');
});