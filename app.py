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
    # Tabela de Militares (com Nome, Nascimento, RG e CPF)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS militares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            rg TEXT UNIQUE NOT NULL,
            cpf TEXT UNIQUE NOT NULL
        )
    ''')
    # Tabela de Respostas das Avaliações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rg_militar TEXT NOT NULL,
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

# 1. ROTA DE CADASTRO (Exclusiva do Gestor Admin)
@app.route('/api/admin/cadastrar-militar', methods=['POST'])
def cadastrar_militar():
    data = request.json
    nome = data.get('nome')
    data_nascimento = data.get('data_nascimento')
    rg = data.get('rg')
    cpf = data.get('cpf')

    if not nome or not data_nascimento or not rg or not cpf:
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios!'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO militares (nome, data_nascimento, rg, cpf) 
            VALUES (?, ?, ?, ?)
        ''', (nome, data_nascimento, rg, cpf))
        conn.commit()
        conn.close()
        return jsonify({'status': 'sucesso', 'mensagem': 'Militar cadastrado com sucesso!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'RG Militar ou CPF já cadastrados!'}), 400

# 2. ROTA DE LOGIN DO MILITAR (Valida se o RG/CPF existe)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identificador = data.get('identificador')  # Pode ser RG ou CPF

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT nome, rg, cpf FROM militares 
        WHERE rg = ? OR cpf = ?
    ''', (identificador, identificador))
    militar = cursor.fetchone()
    conn.close()

    if militar:
        return jsonify({
            'status': 'sucesso', 
            'militar': {'nome': militar[0], 'rg': militar[1], 'cpf': militar[2]}
        })
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Militar não cadastrado no sistema! Solicite o cadastro ao Gestor.'}), 401

# 3. ROTA PARA SALVAR A AVALIAÇÃO
@app.route('/api/salvar', methods=['POST'])
def salvar_resposta():
    data = request.json
    rg_militar = data.get('rg')
    respostas = str(data.get('respostas'))
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO respostas (rg_militar, data_hora, respostas_json) VALUES (?, ?, ?)',
                   (rg_militar, data_hora, respostas))
    conn.commit()
    conn.close()

    return jsonify({'status': 'sucesso', 'mensagem': 'Avaliação enviada com sucesso!'})

# 4. ROTA ADMIN (Listar Militares Cadastrados e Respostas)
@app.route('/api/admin/respostas', methods=['GET'])
def obter_respostas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, m.nome, m.data_nascimento, m.rg, m.cpf, r.data_hora, r.respostas_json 
        FROM respostas r
        JOIN militares m ON r.rg_militar = m.rg
        ORDER BY r.id DESC
    ''')
    registros = cursor.fetchall()
    conn.close()

    lista = []
    for r in registros:
        lista.append({
            'id': r[0],
            'nome': r[1],
            'nascimento': r[2],
            'rg': r[3],
            'cpf': r[4],
            'data_hora': r[5],
            'respostas': r[6]
        })

    return jsonify(lista)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
