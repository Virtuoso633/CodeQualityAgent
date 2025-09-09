#!/bin/bash

echo "🚀 Starting Code Quality Intelligence Web Platform..."

# Set environment variables
export GEMINI_API_KEY="AIzaSyBtnrWXlhRwt_IQJ3XjOTWjRO56SS0hQWs"

# Start services
cd web
docker-compose up --build

echo "✅ Platform is running!"
echo "🌐 Frontend: http://localhost:8501"
echo "🔧 Backend API: http://localhost:8000/docs"
