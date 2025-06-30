@echo off
cd /d C:\xampp\htdocs\church_attendance

REM Optional: Activate virtual environment if used
REM call venv\Scripts\activate

echo Starting Flask server on port 5000...

REM Open default browser
start http://localhost:5000

REM Launch Flask app
python app.py

pause
