import os
import datetime
import logging
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')


active_users = set()
chat_messages = []


def create_log_file(username):
    logs_folder = 'logs'
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'{logs_folder}/{username}_{current_datetime}.txt'

    logging.basicConfig(filename=log_filename, level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] - %(message)s')

    logging.info(f'Session started for user: {username}')

    return log_filename

@app.route('/')
def index():
    if 'username' in session:
        log_filename = create_log_file(session['username'])
        return render_template('index.html', username=session['username'], active_users=active_users, chat_messages=chat_messages, log_filename=log_filename)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        active_users.add(session['username'])
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        active_users.remove(session['username'])
        
        logging.info(f'Session ended for user: {session["username"]}')
        
        session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('message')
def handle_message(msg):
    if 'username' in session:
        logging.info(f'{session["username"]}: {msg}')
        chat_messages.append({'username': session['username'], 'msg': msg})
        room = None
        socketio.emit('message', {'username': session['username'], 'msg': msg}, room=room)
        socketio.emit('update_users', {'active_users': list(active_users)}, room=room)

@socketio.on('connect')
def handle_connect():
    socketio.emit('load_messages', {'chat_messages': chat_messages})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
