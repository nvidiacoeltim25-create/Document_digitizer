#!/bin/bash

echo "Stopping apis.py..."
pkill -f apis.py

echo "Stopping mcp_chat_api.py..."
pkill -f mcp_chat_api.py

echo "Stopping app_face_sign.py..."
pkill -f app_face_sign.py

echo "Stopping MongoDB server..."
sudo systemctl stop mongod

echo "All FastAPI apps and MongoDB server have been stopped."
