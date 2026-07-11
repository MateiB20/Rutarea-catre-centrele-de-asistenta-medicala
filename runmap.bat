@echo off

docker-compose down

docker-compose up --build -d

timeout /t 5 /nobreak > nul

start "" "http://127.0.0.1:8000"

pause