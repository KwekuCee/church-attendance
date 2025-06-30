from flask import Flask, request, jsonify, send_from_directory, redirect, session
from openpyxl import Workbook, load_workbook
from datetime import datetime
import os, random

app = Flask(__name__)
app.secret_key = 'f4b2d8e9c7a14c6f9b8f14a129c2d654'

FILE_NAME = 'attendance.xlsx'
ADMIN_USER = 'admin'
ADMIN_PASS = 'password123'

def generate_code():
    return f"MKC-{random.randint(100, 999)}"

if not os.path.exists(FILE_NAME):
    wb = Workbook()
    ws = wb.active
    ws.append(["Full Name", "Code", "Invited By", "Service Type", "Date", "Time"])
    wb.save(FILE_NAME)

if not os.path.exists("memebrs.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(["Full Name", "Code", "Invited By", "Phone"])
    wb.save("memebrs.xlsx")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    wb_a = load_workbook(FILE_NAME)
    ws_a = wb_a.active

    wb_m = load_workbook("members.xlsx")
    ws_m = wb_m.active

    # Returning Member
    if 'code' in data and data['code']:
        code = data['code'].strip()
        member = None
        for row in ws_m.iter_rows(min_row=2, values_only=True):
            if row[1] == code:
                member = row
                break

        if not member:
            return jsonify({'status': 'error', 'message': 'Code not found'})

        # Prevent duplicate entry for today
        for row in ws_a.iter_rows(min_row=2, values_only=True):
            if row[1] == code and row[5] == today:
                return jsonify({'status': 'error', 'message': 'Already marked attendance for today.'})

        ws_a.append([
            member[0],  # Full Name
            member[1],  # Code
            member[2],  # Invited By
            data.get('service_type', ''),
            member[3],  # Phone
            today,
            now.strftime('%H:%M:%S')
        ])
        wb_a.save(FILE_NAME)
        return jsonify({'status': 'success', 'code': code})

    # New Member
    else:
        fullname = data['fullname'].strip()
        phone = data.get('phone', '').strip()
        invited_by = data.get('invited_by', '').strip()
        service_type = data.get('service_type', '')

        # Check if member already exists
        for row in ws_m.iter_rows(min_row=2, values_only=True):
            if row[0].strip().lower() == fullname.lower() and row[3].strip() == phone:
                return jsonify({'status': 'error', 'message': 'This person already has a code. Use returning member option.'})

        code = generate_code()

        # Save to members file
        ws_m.append([fullname, code, invited_by, phone])
        wb_m.save("members.xlsx")

        # Log attendance
        ws_a.append([
            fullname,
            code,
            invited_by,
            service_type,
            phone,
            today,
            now.strftime('%H:%M:%S')
        ])
        wb_a.save(FILE_NAME)
        return jsonify({'status': 'success', 'code': code})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return send_from_directory('.', 'login.html')
    if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return redirect('/admin')
    return "Invalid login", 401

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')
    return send_from_directory('.', 'admin.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/records')
def records():
    if not session.get('logged_in'):
        return redirect('/login')
    wb = load_workbook(FILE_NAME)
    ws = wb.active
    data = [[cell.value for cell in row] for row in ws.iter_rows(min_row=2)]
    return jsonify(data)

@app.route('/export')
def export():
    if not session.get('logged_in'):
        return redirect('/login')
    return send_from_directory('.', FILE_NAME, as_attachment=True)

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('.', path)

@app.route('/session-status')
def session_status():
    return jsonify({'logged_in': session.get('logged_in', False)})

@app.route('/delete-record', methods=['POST'])
def delete_record():
    if not session.get('logged_in'):
        return redirect('/login')

    data = request.get_json()
    fullname = data['fullname'].strip().lower()
    code = data['code']
    date = data['date']
    time = data['time']

    wb = load_workbook(FILE_NAME)
    ws = wb.active

    row_to_delete = None
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if (row[0] and row[0].strip().lower() == fullname and
            row[1] == code and row[4] == date and row[5] == time):
            row_to_delete = idx
            break

    if row_to_delete:
        ws.delete_rows(row_to_delete)
        wb.save(FILE_NAME)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Record not found'}), 404
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)