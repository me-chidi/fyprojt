#!/bin/bash -e

echo "Resetting the database..."
rm -f database.db
flask db upgrade

echo "Add a user..."
http -b POST http://localhost:5000/users name=john >/dev/null

echo "Get list of users:"
http -b GET http://localhost:5000/users

echo "Add a message..."
http -b POST http://localhost:5000/users/1/messages message=hello >/dev/null

echo "Get list of messages:"
http -b GET http://localhost:5000/messages