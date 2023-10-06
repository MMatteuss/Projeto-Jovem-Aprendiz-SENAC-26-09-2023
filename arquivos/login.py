from flask import Flask, request, render_template, jsonify, make_response, session, redirect, url_for  
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import sql
from io import BytesIO
from reportlab.pdfgen import canvas
import os
import secrets  



app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

# Conexão com o banco (TEM QUE SER POSTGRE)
db_config = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}


#Tela principal
@app.route("/")
def homepage():
    return render_template('index.html')

#Pega o usuário e passa para a outra rota
@app.route("/get_user_name")
def get_user_name():
    # Verifique se o usuário está logado
    if 'user_login' in session:
        user_login = session['user_login']
        
        # Conecte ao banco de dados e execute uma consulta para buscar o nome do usuário
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM usuario WHERE email = %s", (user_login,))
        user_name = cursor.fetchone()[0]  # Supondo que o nome do usuário está na primeira coluna

        cursor.close()
        conn.close()

        return jsonify({"user_name": user_name})

    return jsonify({"user_name": "Visitante"})  # Se o usuário não estiver logado, retorne um valor padrão, como "Visitante"

#Entra na tela para escolher a área (Aluno, empresa ou Senac)
@app.route("/telaprincipal", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Consulta para checar e-mail e senha
        query = sql.SQL("SELECT * FROM usuario WHERE email = %s AND senha = %s")
        cursor.execute(query, (email, senha))
        user = cursor.fetchone()
        conn.close()

        #Caso as credenciais do usuário estejam corretas, o programa desce para este bloco
        if user:
            session['user_login'] = user[0]  # Supondo que o login do usuário está na primeira posição da tupla (índice 0)
            # Abre o arquivo HTML já com as vagas cadastradas
            return render_template('homepage.html') 
            
        else:
            # Se alguma coisa der errado, ele vai chamar esta página de erro. Exemplo: Se o usuário digitar a senha errada
            return render_template("erro.html")

@app.route("/perfil_aluno")
def perfil():
    # Verifique se o usuário está autenticado
    if 'user_login' not in session:
        return redirect(url_for('login'))  # Redirecionar para a página de login se não estiver autenticado

    # Recupere o login do usuário da sessão
    user_login = session['user_login']

    # Conecte ao banco de dados e execute uma consulta para obter os dados do usuário
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email, cidade, cpf, curso FROM aluno WHERE email = %s", (user_login,))
    user_data = cursor.fetchone()  # Recupere o primeiro registro encontrado

    cursor.close()
    conn.close()

    # Verifique se os dados do usuário foram encontrados
    if user_data:
        # Os dados do usuário foram encontrados, renderize a página de perfil com os dados
        return render_template('perfil.html', user_data=user_data)
    else:
        # Se os dados do usuário não foram encontrados, você pode redirecionar para uma página de erro ou fazer algo diferente
        return render_template('erro.html')  # Redirecione para uma página de erro, por exemplo

@app.route("/voltar")
def voltar():
  return render_template('homepage.html')


#Entra na área da emresa. A empresa visualiza o mural de vagas e visualiza o cadastro de vagas
@app.route("/area_empresa", methods=["GET", "POST"])
def area_empresa():
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Executa uma consulta para buscar os registros da tabela "empresa", que é onde estão as vagas cadastradas
        cursor.execute("SELECT nome_empresa, descricao_empresa FROM vagas")

        # Obtém os resultados da consulta
        empresas = cursor.fetchall()

        # Consulta para trazer as empresas cadastradas no lisbox
        query3 = sql.SQL("SELECT nome_empresa FROM empresa")
        cursor.execute(query3)
        cadastradas = cursor.fetchall()

        # Fecha a conexão com o banco de dados
        cursor.close()
        conn.close()

        # Abre o arquivo HTML já com as vagas cadastradeas
        return render_template('area_empresa.html', empresas=empresas, cadastradas=cadastradas) 
        #return render_template("vagas.html")

        


#Entra na área do aluno. O aluno visualiza as vagas, mas não visualiza o cadastro de vagas
@app.route("/area_aluno")
def area_aluno():
        # Conecta ao banco de dados
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Executa uma consulta para buscar os registros da tabela "empresa", que é onde estão as vagas cadastradas
        cursor.execute("SELECT nome_empresa, descricao_empresa FROM vagas")

        # Obtém os resultados da consulta
        empresas = cursor.fetchall()

        # Fecha a conexão com o banco de dados
        cursor.close()
        conn.close()

        # Abre o arquivo HTML já com as vagas cadastradeas
        return render_template('area_aluno.html', empresas=empresas) 
        #return render_template("vagas.html")
 



#Entra na área do Senac. O Senac visualiza o mural de vagas e visualiza o cadastro de vagas
@app.route("/area_senac")
def area_senac():
        # Conecta ao banco de dados
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Executa uma consulta para buscar os registros da tabela "empresa", que é onde estão as vagas cadastradas
        cursor.execute("SELECT nome_empresa, descricao_empresa FROM vagas")

        # Obtém os resultados da consulta
        empresas = cursor.fetchall()

        # Consulta para trazer as empresas cadastradas no lisbox
        query2 = sql.SQL("SELECT nome_empresa FROM empresa")
        cursor.execute(query2)
        cadastradas = cursor.fetchall()

        # Fecha a conexão com o banco de dados
        cursor.close()
        conn.close()

        # Abre o arquivo HTML já com as vagas cadastradeas
        return render_template('area_senac.html', empresas=empresas, cadastradas=cadastradas) 
        #return render_template("vagas.html")





# Cadastro das áreas profissionais que estarão disponíveis no sistema para o aluno escolher
@app.route("/cadarea")
def cadarea():
    return render_template('cadarea.html')


@app.route("/cadarea_insert", methods=['POST'])
def cadarea_insert():
    if request.method == 'POST':
        nome_area = request.form['nome_area']


        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Consulta para checar e-mail e senha
        cursor.execute("INSERT INTO areaprofissional (nome_area) VALUES (%s)", (nome_area,))

        conn.commit()
        cursor.close()  # Fechando o cursor
        conn.close()  # Fechando a conexão

        return render_template('cadarea_sucesso.html')




#CADASTRO DAS VAGAS NO MURAL DE VAGAS
@app.route('/insert_content', methods=['POST'])
def insert_content():
    data = request.get_json()
    
    if "new_content" in data and data["new_content"].strip() != "":
        new_content = data["new_content"]
        selected_optionValue = data.get("selected_option", "")  # Recupere a opção selecionada, se existir

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vagas (descricao_empresa, nome_empresa) VALUES (%s, %s)", (new_content, selected_optionValue))
        conn.commit()
        conn.close()

        # Recuperar os registros atualizados
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vagas")
        empresas = cursor.fetchall()
        conn.close()

        return jsonify(empresas)

    return jsonify({"error": "Conteúdo vazio."}), 400




# Relação (num grid) dos alunos cadastrados
@app.route('/grid', methods=['GET', 'POST'])
def grid():
    results_name = []           
    results_professional_area = []
    if request.method == 'POST':
        search_name = request.form.get('search_name')
        search_professional_area = request.form.get('search_professional_area')
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM aluno")
        result = cursor.fetchall()
        if search_name:
            cursor.execute("SELECT nome_aluno, curso_aluno FROM aluno WHERE nome_aluno ILIKE %s", ('%' + search_name + '%',))
            results_name = cursor.fetchall()
                

        if search_professional_area:
            cursor.execute("SELECT nome_aluno, curso_aluno FROM aluno WHERE curso_aluno ILIKE %s", ('%' + search_professional_area + '%',))
            results_professional_area = cursor.fetchall()

        conn.close()  # Fechando a conexão
        return render_template('grid.html', result=result, results_name=results_name, results_professional_area=results_professional_area)
        # return render_template('grid.html', result=result)
    else:
        return render_template('grid.html', result=None)
        # return render_template('grid.html', result=None)




@app.route('/anteslistacadastrados', methods=['GET'])
def anteslistacadastrados():
   return render_template('filtroaluno.html')



@app.route('/listacadastrados', methods=['GET', 'POST'])
def listacadastrados():
    results_name = []
    results_professional_area = []

    if request.method == 'POST':
        search_name = request.form.get('search_name')
        search_professional_area = request.form.get('search_professional_area')
        connection = psycopg2.connect(**db_config)

        cursor = connection.cursor()

        if search_name:
            cursor.execute("SELECT nome, curso FROM aluno WHERE nome ILIKE %s", ('%' + search_name + '%',))
            results_name = cursor.fetchall()

        if search_professional_area:
            cursor.execute("SELECT nome, curso FROM aluno WHERE curso ILIKE %s", ('%' + search_professional_area + '%',))
            results_professional_area = cursor.fetchall()

        connection.close()

    return render_template('filtroaluno.html', results_name=results_name, results_professional_area=results_professional_area)




@app.route('/gerar_pdf')
def gerar_pdf():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM aluno")
    dados = cursor.fetchall()
    conn.close()

    # Crie um objeto BytesIO para armazenar o PDF em memória
    pdf_buffer = BytesIO()

    # Use o ReportLab para criar o PDF
    p = canvas.Canvas(pdf_buffer)
    p.drawString(100, 750, "Relatório de Alunos")
    
    y = 700
    for dado in dados:
        y -= 20
        p.drawString(100, y, f"Nome: {dado[0]}, Idade: {dado[1]}")  # Altere isso para se adequar aos seus dados

    p.showPage()
    p.save()

    # Defina os cabeçalhos da resposta
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=relatorio.pdf'

    return response



@app.route('/cadastroaluno')
def cadastroaluno():
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Executa uma consulta para buscar os registros da tabela "empresa", que é onde estão as vagas cadastradas
        dados = sql.SQL("SELECT nome_curso FROM curso")
        cursor.execute(dados)
        cursos = cursor.fetchall()
        
        # cadastradas = cursor.fetchall()

        # Fecha a conexão com o banco de dados
        cursor.close()
        conn.close()

        # Abre o arquivo HTML já com as vagas cadastradeas
        return render_template('cadastroaluno.html', cursos=cursos)
        #return render_template("vagas.html")
    

 
@app.route('/cadastroaluno_insert', methods=['POST'])
#POST: método para enviar dados do cliente para o servidor
#GET: método onde o cliente solicita dados do servidor
#REQUEST: método de requisição. É um método que faz requisições HTTP (protocolo)

def cadastroaluno_insert():
    if request.method == 'POST':
       nome = request.form['NOME']
       cpf = request.form['CPF']
       cidade = request.form['ESTADO']
       curso = request.form['CURSO']
       email = request.form['EMAIL']
       senha = request.form['senha']


       conn = psycopg2.connect(**db_config)
       cursor = conn.cursor()
       cursor.execute("INSERT INTO aluno (nome, cpf, estado, curso, email, senha) VALUES (%s, %s, %s, %s, %s, %s)", (nome, cpf, cidade, curso, email, senha))
       conn.commit()
       cursor.close()  # Fechando o cursor
       conn.close()  # Fechando a conexão

       return render_template('/cadastroaluno_sucesso.html')
    



        



@app.route("/cadastroempresa", methods=["GET", "POST"])
def cadastroempresa():
    return render_template('cadempresas.html')

@app.route('/cadempresas', methods=["GET", "POST"])
def cadempresas():
    if request.method == 'POST':
        nome = request.form['nome_empresa']
        cnpj = request.form['cnpj']
        rua = request.form['rua']
        numero = request.form['numero']
        bairro = request.form['bairro']
        cidade = request.form['cidade']
        email = request.form['email']
        cep = request.form['cep']
        estado = request.form['estado']
        celular = request.form['celular']
        

        conexao = psycopg2.connect(**db_config)
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO empresa (nome_empresa, cnpj, rua, numero, bairro, cidade, email, cep, estado, celular) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (nome, cnpj, rua, numero, bairro, cidade, email, cep, estado, celular))
        conexao.commit()
        cursor.close()
        conexao.close()

        return render_template('cadempresas_sucesso.html')
    

@app.route("/entrausuario", methods=["GET", "POST"])
def entrausuario():
  return render_template('usuario.html')


@app.route("/usuario", methods=["GET", "POST"])
def usuario():
    if request.method == 'POST':
        nome = request.form['NOME']
        perfil = request.form['PERFIL']
        cpf = request.form['CPF']
        email = request.form['EMAIL']
        senha = request.form['SENHA']

        conexao = psycopg2.connect(**db_config)
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO usuario (nome, perfil, cpf, email, senha) VALUES (%s, %s, %s, %s, %s)", (nome, perfil, cpf, email, senha))
        conexao.commit()
        cursor.close()  # Fechando o cursor
        conexao.close()  # Fechando a conexão

        return render_template('usuario_sucesso.html')     

#============= FILTRO EMPRESA ==============
@app.route('/filtroaluno', methods=['GET', 'POST'])
def filtroaluno():
    results_name = []           
    results_professional_area = []
    results_email = []
    results_cidade = []

    if request.method == 'POST':
        search_name = request.form.get('search_name')
        search_professional_area = request.form.get('search_professional_area')
        search_email = request.form.get('search_email')
        search_cidade = request.form.get('search_cidade')
        
        connection = psycopg2.connect(**db_config)

        cursor = connection.cursor()

        if search_name:
            cursor.execute("SELECT nome, curso, email, cidade, cpf FROM aluno WHERE nome ILIKE %s", ('%' + search_name + '%',))
            results_name = cursor.fetchall()
            
        if search_professional_area:
            cursor.execute("SELECT nome FROM aluno WHERE curso ILIKE %s", ('%' + search_professional_area + '%',))
            results_professional_area = cursor.fetchall()
        
            if search_email:
                cursor.execute("SELECT email, cidade, cpf FROM aluno WHERE email")
                results_email = cursor.fetchall()
    
                if search_cidade:
                    cursor.execute("SELECT cidade, cpf FROM aluno WHERE cidade")
                    results_cidade = cursor.fetchall()
                

        if search_professional_area:
            cursor.execute("SELECT nome, curso, email, cidade, cpf FROM aluno WHERE curso ILIKE %s", ('%' + search_professional_area + '%',))
            results_professional_area = cursor.fetchall()
        
            if search_email:
                cursor.execute("SELECT email, cidade, cpf FROM aluno WHERE email")
                results_email = cursor.fetchall()
        
                if search_cidade:
                    cursor.execute("SELECT cidade, cpf FROM aluno WHERE cidade")
                    results_cidade = cursor.fetchall()

        connection.close() 

    return render_template('filtroaluno_2.html', results_name=results_name, results_professional_area=results_professional_area, results_email=results_email, results_cidade=results_cidade)



# Grid

#====RECUPERAR CONTA===
@app.route('/recuperarconta', methods=['GET', 'POST'])
def recuperarconta():
    result_cpf = []
    resultado = []
    

    if request.method == 'POST':
        cpf = request.form.get('cpf')
        connection = psycopg2.connect(**db_config)
        senha = request.form.get['senha']

        cursor = connection.cursor()

        cursor.execute('Select * FROM aluno WHERE escolaridade = "Ensino medio completo" AND cpf like %s', ('%' + cpf + '%'))
        resultado = cursor.fetchall()
        if cpf:

            cursor.execute("SELECT cpf FROM aluno %s", (cpf))
            result_cpf = cursor.fetchall()

            if result_cpf==resultado:
                conexao = psycopg2.connect(**db_config)
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO aluno (senha) VALUES (%s)", (senha))
                conexao.commit()
                cursor.close()  # Fechando o cursor
                conexao.close() 
                return render_template('senhanova.html')
        connection.close()

    return render_template('recCONTA.html', result_cpf=result_cpf)










# ========== PERFIL SELECIONADO /(NAME) ========
@app.route("/perfil_selecionado/<nome_usuario>", methods=["GET", "POST"])
def perfil_selecionado(nome_usuario):
    resultado_selecionados = []
    # Verifique se o usuário está autenticado
    if  request.method == 'POST':
        resultado_selecionados = request.form.get('nome_usuario')
        resultado_selecionados = nome_usuario
        
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        if nome_usuario:    
            cursor.execute("SELECT nome FROM aluno %s", ('%' + nome_usuario + '%',))
            resultado_selecionados = cursor.fetchone()
            
    return render_template('perfil.html', resultado_selecionados=resultado_selecionados)





if __name__ == "__main__":
    app.run(debug=True, port=8085, host='127.0.0.2')
