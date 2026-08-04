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
    # Tabela de Militares Cadastrados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS militares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            rg TEXT UNIQUE NOT NULL,
            matricula TEXT UNIQUE NOT NULL
        )
    ''')
    # Tabela de Respostas
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

# 1. ROTA DE CADASTRO DO MILITAR
@app.route('/api/cadastrar', methods=['POST'])
def cadastrar():
    data = request.json
    nome = data.get('nome')
    rg = data.get('rg')
    matricula = data.get('matricula')

    if not nome or not rg or not matricula:
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios!'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO militares (nome, rg, matricula) VALUES (?, ?, ?)', (nome, rg, matricula))
        conn.commit()
        conn.close()
        return jsonify({'status': 'sucesso', 'mensagem': 'Cadastro realizado com sucesso!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'RG ou Matrícula já cadastrados no sistema!'}), 400

# 2. ROTA DE LOGIN (VALIDAÇÃO)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    matricula = data.get('matricula')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT nome, rg FROM militares WHERE matricula = ?', (matricula,))
    militar = cursor.fetchone()
    conn.close()

    if militar:
        return jsonify({
            'status': 'sucesso', 
            'militar': {'nome': militar[0], 'rg': militar[1], 'matricula': matricula}
        })
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Militar não cadastrado! Faça o cadastro primeiro.'}), 401

# 3. ROTA PARA SALVAR A PROVA
@app.route('/api/salvar', methods=['POST'])
def salvar_resposta():
    data = request.json
    matricula = data.get('matricula')
    respostas = str(data.get('respostas'))
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO respostas (matricula, data_hora, respostas_json) VALUES (?, ?, ?)',
                   (matricula, data_hora, respostas))
    conn.commit()
    conn.close()

    return jsonify({'status': 'sucesso', 'mensagem': 'Avaliação enviada com sucesso!'})

# 4. ROTA ADMIN (LISTAR MILITARES E RESPOSTAS)
@app.route('/api/admin/respostas', methods=['GET'])
def obter_respostas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, m.nome, m.rg, r.matricula, r.data_hora, r.respostas_json 
        FROM respostas r
        JOIN militares m ON r.matricula = m.matricula
        ORDER BY r.id DESC
    ''')
    registros = cursor.fetchall()
    conn.close()

    lista = []
    for r in registros:
        lista.append({
            'id': r[0],
            'nome': r[1],
            'rg': r[2],
            'matricula': r[3],
            'data_hora': r[4],
            'respostas': r[5]
        })

    return jsonify(lista)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
