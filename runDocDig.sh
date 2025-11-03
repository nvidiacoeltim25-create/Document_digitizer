#!/bin/bash

cd "$(dirname "$0")"

echo "Starting MongoDB server..."
sudo systemctl start mongod

echo "Starting apis.py in 'verification' environment..."
nohup conda run -n verification python apis.py > apis.log 2>&1 &

echo "Starting mcp_chat_api.py in 'ddmcpenv' environment..."
nohup conda run -n ddmcpenv python mcp_client/mcp_chat_api.py > mcp_chat_api.log 2>&1 &

echo "Starting app_face_sign.py in 'comparison' environment..."
nohup conda run -n comparison python ml_face_sign_client/app_face_sign.py > app_face_sign.log 2>&1 &

echo "All FastAPI apps and MongoDB server launched. Check *.log files for output."
