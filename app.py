from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # Tabela de Militares Cadastrados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS militares (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            rg TEXT UNIQUE NOT NULL,
            funcao TEXT
        )
    ''')

    # Migração: remove a coluna cpf caso ainda exista de uma versão anterior do banco,
    # e adiciona a coluna funcao caso o banco já exista de uma versão sem ela
    cursor.execute('ALTER TABLE militares DROP COLUMN IF EXISTS cpf')
    cursor.execute('ALTER TABLE militares ADD COLUMN IF NOT EXISTS funcao TEXT')

    # Tabela de Respostas dos Militares
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id SERIAL PRIMARY KEY,
            rg_militar TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            respostas_json TEXT NOT NULL
        )
    ''')

    # Tabela de Perguntas da Prova
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perguntas (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            tempo INTEGER NOT NULL,
            opcoes_json TEXT
        )
    ''')

    # Se a tabela de perguntas estiver vazia, carrega as 19 questões padrão
    cursor.execute('SELECT COUNT(*) FROM perguntas')
    count = cursor.fetchone()[0]

    if count < 19:
        cursor.execute('DELETE FROM perguntas')  # Reseta para garantir a lista completa de 1 a 19
        perguntas_19 = [
            ("mc", "1. Qual é o principal objetivo do atendimento realizado pela Central 193?", 120, json.dumps(["Registrar reclamações administrativas.", "Prestar informações turísticas.", "Receber, qualificar e despachar ocorrências de emergência.", "Elaborar relatórios estatísticos."])),
            ("mc", "2. Ao atender uma ligação, a primeira informação que deve ser confirmada é:", 120, json.dumps(["Nome do comandante da área.", "Endereço exato da ocorrência.", "Quantidade de viaturas disponíveis.", "Número de matrícula do atendente."])),
            ("open", "3. O que caracteriza uma ocorrência de salvamento?", 420, json.dumps([])),
            ("mc", "4. Em uma ligação de incêndio em residência, qual dado é prioritário para o despacho?", 120, json.dumps(["Cor da casa.", "Presença de vítimas presas ou feridas.", "Valor estimado do imóvel.", "Nome do proprietário."])),
            ("mc", "5. Qual é a conduta correta caso o solicitante esteja extremamente nervoso?", 120, json.dumps(["Desligar a ligação.", "Manter a calma, usar tom firme e acolhedor e focar nas perguntas objetivas.", "Discutir com o solicitante.", "Transferir a ligação imediatamente sem colher dados."])),
            ("mc", "6. O termo 'Triage' no atendimento operacional refere-se a:", 120, json.dumps(["Classificação dos atendentes por antiguidade.", "Priorização das ocorrências de acordo com a gravidade.", "Organização dos horários de serviço.", "Limpeza das estações de trabalho."])),
            ("open", "7. Cite três perguntas essenciais a serem feitas em um caso de acidente de trânsito.", 420, json.dumps([])),
            ("mc", "8. Qual tipo de ocorrência exige despacho imediato, mesmo com informações incompletas?", 120, json.dumps(["Perturbação do sossego.", "Incêndio com vítimas presas ou colapso de estrutura.", "Vistoria preventiva.", "Corte de árvore sem risco iminente."])),
            ("mc", "9. Quando uma ligação é considerada trote, a atitude operacional padronizada é:", 120, json.dumps(["Agredir verbalmente o chamador.", "Alertar sobre a gravidade do ato, encerrar a ligação e registrar no sistema.", "Ignorar e deixar a linha aberta.", "Enviar viatura mesmo assim."])),
            ("mc", "10. A sigla CBMERJ significa:", 120, json.dumps(["Centro de Bombeiros Militares do Estado do Rio de Janeiro.", "Corpo de Bombeiros Militar do Estado do Rio de Janeiro.", "Comando de Bombeiros e Resgate do Rio de Janeiro.", "Companhia de Bombeiros Municipais do Rio de Janeiro."])),
            ("mc", "11. Qual é a principal função do despachante na Central 193?", 120, json.dumps(["Atender a todas as chamadas do público.", "Selecionar e enviar os recursos/viaturas adequados para a ocorrência.", "Fazer a manutenção dos rádios.", "Atender a imprensa."])),
            ("mc", "12. O que deve ser feito ao receber uma chamada sobre vazamento de gás em local fechado?", 120, json.dumps(["Orientar a acender as luzes para verificar a vazamento.", "Orientar a evacuar o local, não acionar interruptores e despachar socorro.", "Pedir ao solicitante para procurar a origem do vazamento com fósforo.", "Aguardar 30 minutos antes de enviar viatura."])),
            ("open", "13. Descreva sucintamente o procedimento diante de uma chamada de afogamento em andamento.", 420, json.dumps([])),
            ("mc", "14. Qual código/linguagem é utilizado no rádio para padronizar as comunicações operacionais?", 120, json.dumps(["Código Morse.", "Código Q e Alfabeto Fonético (Phonetic Alphabet).", "Linguagem de sinais.", "Gírias locais."])),
            ("mc", "15. Em caso de múltiplas chamadas para o mesmo evento, o atendente deve:", 120, json.dumps(["Desprezar as novas chamadas.", "Agrupar as informações no mesmo registro de ocorrência.", "Criar uma nova ocorrência para cada ligação sem vincular.", "Mandar uma viatura para cada ligação."])),
            ("mc", "16. Qual é a viatura típica para combate a incêndio urbano no CBMERJ?", 120, json.dumps(["ASE (Auto Socorro de Emergência).", "ABT (Auto Bomba Tanque).", "AR (Auto Resgate).", "APK (Auto Plataforma Mecânica)."])),
            ("open", "17. Explique a diferença entre emergência e urgência no contexto do atendimento 193.", 420, json.dumps([])),
            ("mc", "18. O registro preciso do horário de cada etapa da ocorrência é importante para:", 120, json.dumps(["Apenas controle de ponto dos militares.", "Auditoria, estatística operacional e histórico jurídico da ocorrência.", "Preencher espaço no sistema.", "Escolher quem vai para a próxima ocorrência."])),
            ("mc", "19. Se o sistema informatizado sair do ar durante o plantão, a conduta correta é:", 120, json.dumps(["Parar o atendimento até o sistema voltar.", "Acionar o plano de contingência (registro manual/fichas físicas) e manter o atendimento.", "Mandar o público ligar para a Polícia Militar.", "Encerrar o plantão antecipadamente."]))
        ]
        cursor.executemany(
            'INSERT INTO perguntas (tipo, enunciado, tempo, opcoes_json) VALUES (%s, %s, %s, %s)',
            perguntas_19
        )

    conn.commit()
    cursor.close()
    conn.close()


init_db()


@app.route('/')
def home():
    return "Servidor CBMERJ 193 Online com 19 Questões (Postgres/Supabase)!", 200


# ROTA DE LOGIN DO MILITAR
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    rg = data.get('rg')

    if not rg:
        return jsonify({'status': 'erro', 'mensagem': 'Informe o RG Militar!'}), 400

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT nome, rg, funcao FROM militares WHERE rg = %s', (rg,))
    militar = cursor.fetchone()
    cursor.close()
    conn.close()

    if militar:
        return jsonify({
            'status': 'sucesso',
            'militar': {'nome': militar[0], 'rg': militar[1], 'funcao': militar[2]}
        })
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Acesso negado! RG Militar não cadastrado.'}), 401


# ROTA PARA BUSCAR AS PERGUNTAS DA PROVA
@app.route('/api/perguntas', methods=['GET'])
def obter_perguntas():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id, tipo, enunciado, tempo, opcoes_json FROM perguntas ORDER BY id ASC')
    rows = cursor.fetchall()
    cursor.close()
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


# ROTA PARA SALVAR RESPOSTAS DO QUIZ
@app.route('/api/salvar', methods=['POST'])
def salvar_resposta():
    data = request.json
    rg_militar = data.get('rg')
    respostas = json.dumps(data.get('respostas'))
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO respostas (rg_militar, data_hora, respostas_json) VALUES (%s, %s, %s)',
        (rg_militar, data_hora, respostas)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'sucesso', 'mensagem': 'Avaliação enviada com sucesso!'})


# ROTAS ADMINISTRATIVAS DO GESTOR

@app.route('/api/admin/militares', methods=['GET'])
def listar_militares():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, data_nascimento, rg, funcao FROM militares ORDER BY nome ASC')
    militares = cursor.fetchall()
    cursor.close()
    conn.close()

    lista = [{'id': m[0], 'nome': m[1], 'nascimento': m[2], 'rg': m[3], 'funcao': m[4]} for m in militares]
    return jsonify(lista)


@app.route('/api/admin/salvar-militar', methods=['POST'])
def salvar_militar():
    data = request.json
    m_id = data.get('id')
    nome = data.get('nome')
    nascimento = data.get('data_nascimento')
    rg = data.get('rg')
    funcao = data.get('funcao')

    if not nome or not nascimento or not rg or not funcao:
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios!'}), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        if m_id:
            cursor.execute(
                'UPDATE militares SET nome=%s, data_nascimento=%s, rg=%s, funcao=%s WHERE id=%s',
                (nome, nascimento, rg, funcao, m_id)
            )
            mensagem = "Militar atualizado com sucesso!"
        else:
            cursor.execute(
                'INSERT INTO militares (nome, data_nascimento, rg, funcao) VALUES (%s, %s, %s, %s)',
                (nome, nascimento, rg, funcao)
            )
            mensagem = "Militar cadastrado com sucesso!"

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'sucesso', 'mensagem': mensagem})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'RG Militar já cadastrado!'}), 400


@app.route('/api/admin/excluir-militar/<int:id_militar>', methods=['DELETE'])
def excluir_militar(id_militar):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM militares WHERE id = %s', (id_militar,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Militar removido.'})


@app.route('/api/admin/salvar-pergunta', methods=['POST'])
def salvar_pergunta():
    data = request.json
    p_id = data.get('id')
    tipo = data.get('tipo')
    enunciado = data.get('enunciado')
    tempo = data.get('tempo')
    opcoes = json.dumps(data.get('opcoes', []))

    conn = get_conn()
    cursor = conn.cursor()

    if p_id:
        cursor.execute(
            'UPDATE perguntas SET tipo=%s, enunciado=%s, tempo=%s, opcoes_json=%s WHERE id=%s',
            (tipo, enunciado, tempo, opcoes, p_id)
        )
    else:
        cursor.execute(
            'INSERT INTO perguntas (tipo, enunciado, tempo, opcoes_json) VALUES (%s, %s, %s, %s)',
            (tipo, enunciado, tempo, opcoes)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Pergunta salva com sucesso!'})


@app.route('/api/admin/excluir-pergunta/<int:id_pergunta>', methods=['DELETE'])
def excluir_pergunta(id_pergunta):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM perguntas WHERE id = %s', (id_pergunta,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'sucesso', 'mensagem': 'Pergunta excluída.'})


@app.route('/api/admin/respostas', methods=['GET'])
def obter_respostas():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, m.nome, m.data_nascimento, m.rg, m.funcao, r.data_hora, r.respostas_json
        FROM respostas r
        JOIN militares m ON r.rg_militar = m.rg
        ORDER BY r.id DESC
    ''')
    registros = cursor.fetchall()
    cursor.close()
    conn.close()

    lista = []
    for r in registros:
        lista.append({
            'id': r[0],
            'nome': r[1],
            'nascimento': r[2],
            'rg': r[3],
            'funcao': r[4],
            'data_hora': r[5],
            'respostas': json.loads(r[6])
        })

    return jsonify(lista)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
