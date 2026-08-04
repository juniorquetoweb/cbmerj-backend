from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import json
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
            data_nascimento TEXT NOT NULL,
            rg TEXT UNIQUE NOT NULL,
            cpf TEXT UNIQUE NOT NULL
        )
    ''')
    # Tabela de Respostas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rg_militar TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            respostas_json TEXT NOT NULL
        )
    ''')
    # Tabela de Perguntas da Prova
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            tempo INTEGER NOT NULL,
            opcoes_json TEXT
        )
    ''')
    
    # Inserir perguntas padrão se a tabela estiver vazia
    cursor.execute('SELECT COUNT(*) FROM perguntas')
    if cursor.fetchone()[0] == 0:
        perguntas_iniciais = [
            ("mc", "1. Qual é o principal objetivo do atendimento realizado pela Central 193?", 120, json.dumps(["Registrar reclamações administrativas.", "Prestar informações turísticas.", "Receber, qualificar e despachar ocorrências de emergência.", "Elaborar relatórios estatísticos."])),
            ("mc", "2. Ao atender uma ligação, a primeira informação que deve ser confirmada é:", 120, json.dumps(["Nome do comandante da área.", "Endereço exato da ocorrência.", "Quantidade de viaturas disponíveis.", "Número de matrícula do atendente."])),
            ("open", "3. O que caracteriza uma ocorrência de salvamento?", 420, json.dumps([]))
        ]
        cursor.executemany('INSERT INTO perguntas (tipo, enunciado, tempo, opcoes_json) VALUES (?, ?, ?, ?)', perguntas_iniciais)

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Servidor CBMERJ 193 Online!", 200

# 1. ROTA DE LOGIN DO MILITAR
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    rg = data.get('rg')

    if not rg:
        return jsonify({'status': 'erro', 'mensagem': 'Informe o RG Militar!'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT nome, rg, cpf FROM militares WHERE rg = ?', (rg,))
    militar = cursor.fetchone()
    conn.close()

    if militar:
        return jsonify({
            'status': 'sucesso', 
            'militar': {'nome': militar[0], 'rg': militar[1], 'cpf': militar[2]}
        })
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Acesso negado! RG Militar não cadastrado. Solicite ao Gestor.'}), 401

# 2. ROTA DE PERGUNTAS (OBTER PERGUNTAS PARA O MILITAR)
@app.route('/api/perguntas', methods=['GET'])
def obter_perguntas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, tipo, enunciado, tempo, opcoes_json FROM perguntas')
    rows = cursor.fetchall()
    conn.close()

    lista = []
    for r in rows:
        lista.append({
            'id': r[0],
            'type': r[1],
            'q': r[2],
            'time': r[3],
            'options': json.loads(r[4]) if r[4] else []
        })

    return jsonify(lista)

# 3. ROTA PARA SALVAR A AVALIAÇÃO DO MILITAR
@app.route('/api/salvar', methods=['POST'])
def salvar_resposta():
    data = request.json
    rg_militar = data.get('rg')
    respostas = json.dumps(data.get('respostas'))
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO respostas (rg_militar, data_hora, respostas_json) VALUES (?, ?, ?)',
                   (rg_militar, data_hora, respostas))
    conn.commit()
    conn.close()

    return jsonify({'status': 'sucesso', 'mensagem': 'Avaliação enviada com sucesso!'})

# --- ROTAS EXCLUSIVAS DO GESTOR ADMIN ---

# 4. LISTAR MILITARES
@app.route('/api/admin/militares', methods=['GET'])
def listar_militares():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, data_nascimento, rg, cpf FROM militares ORDER BY nome ASC')
    militares = cursor.fetchall()
    conn.close()

    lista = [{'id': m[0], 'nome': m[1], 'nascimento': m[2], 'rg': m[3], 'cpf': m[4]} for m in militares]
    return jsonify(lista)

# 5. CADASTRAR / EDITAR MILITAR
@app.route('/api/admin/salvar-militar', methods=['POST'])
def salvar_militar():
    data = request.json
    m_id = data.get('id')
    nome = data.get('nome')
    nascimento = data.get('data_nascimento')
    rg = data.get('rg')
    cpf = data.get('cpf')

    if not nome or not nascimento or not rg or not cpf:
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios!'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        if m_id: # Edição
            cursor.execute('''
                UPDATE militares SET nome=?, data_nascimento=?, rg=?, cpf=? WHERE id=?
            ''', (nome, nascimento, rg, cpf, m_id))
            mensagem = "Militar atualizado com sucesso!"
        else: # Novo Cadastro
            cursor.execute('''
                INSERT INTO militares (nome, data_nascimento, rg, cpf) VALUES (?, ?, ?, ?)
            ''', (nome, nascimento, rg, cpf))
            mensagem = "Militar cadastrado com sucesso!"

        conn.commit()
        conn.close()
        return jsonify({'status': 'sucesso', 'mensagem': mensagem})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'RG Militar ou CPF já em uso por outro cadastro!'}), 400

# 6. EXCLUIR MILITAR
@app.route('/api/admin/excluir-militar/<int:id_militar>', methods=['DELETE'])
def excluir_militar(id_militar):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM militares WHERE id = ?', (id_militar,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Militar removido.'})

# 7. ADICIONAR / EDITAR PERGUNTA
@app.route('/api/admin/salvar-pergunta', methods=['POST'])
def salvar_pergunta():
    data = request.json
    p_id = data.get('id')
    tipo = data.get('tipo')
    enunciado = data.get('enunciado')
    tempo = data.get('tempo')
    opcoes = json.dumps(data.get('opcoes', []))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if p_id:
        cursor.execute('UPDATE perguntas SET tipo=?, enunciado=?, tempo=?, opcoes_json=? WHERE id=?',
                       (tipo, enunciado, tempo, opcoes, p_id))
    else:
        cursor.execute('INSERT INTO perguntas (tipo, enunciado, tempo, opcoes_json) VALUES (?, ?, ?, ?)',
                       (tipo, enunciado, tempo, opcoes))

    conn.commit()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Pergunta salva com sucesso!'})

# 8. EXCLUIR PERGUNTA
@app.route('/api/admin/excluir-pergunta/<int:id_pergunta>', methods=['DELETE'])
def excluir_pergunta(id_pergunta):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM perguntas WHERE id = ?', (id_pergunta,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Pergunta excluída com sucesso!'})

# 9. OBTER RESPOSTAS DOS MILITARES
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
            'respostas': json.loads(r[6])
        })

    return jsonify(lista)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
