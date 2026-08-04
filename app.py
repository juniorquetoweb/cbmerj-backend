from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "cbmerj_online.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            respostas_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Servidor CBMERJ 193 Online!", 200

@app.route('/api/salvar', methods=['POST'])
def salvar_resposta():
    data = request.json
    matricula = data.get('matricula')
    respostas = str(data.get('respostas'))
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    if not matricula:
        return jsonify({'status': 'erro', 'mensagem': 'Matrícula ausente'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO respostas (matricula, data_hora, respostas_json) VALUES (?, ?, ?)',
                   (matricula, data_hora, respostas))
    conn.commit()
    conn.close()

    return jsonify({'status': 'sucesso', 'mensagem': 'Gravado na nuvem!'})

@app.route('/api/admin/respostas', methods=['GET'])
def obter_respostas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, matricula, data_hora, respostas_json FROM respostas ORDER BY id DESC')
    registros = cursor.fetchall()
    conn.close()

    lista = []
    for r in registros:
        lista.append({
            'id': r[0],
            'matricula': r[1],
            'data_hora': r[2],
            'respostas': r[3]
        })

    return jsonify(lista)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
