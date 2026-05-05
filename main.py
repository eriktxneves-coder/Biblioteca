from os import name

import customtkinter as ctk
#from login import verificar_login
import sqlite3
from PIL import Image
import datetime
from tkinter import messagebox
import requests
from io import BytesIO
import bcrypt

ctk.set_appearance_mode("dark")

usuario_logado = None

def gerar_hash(senha):
    senha_bytes = senha.encode("utf-8")
    salt = bcrypt. gensalt()
    hash_senha = bcrypt.hashpw(senha_bytes, salt)
    return hash_senha
    print("hash_senha")
    
def verificar_senha(senha_digitada, senha_hash):
    return bcrypt.checkpw(senha_digitada.encode("utf-8"), senha_hash)



def carregar_imagem_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except:
        print("Erro ao carregar imagem")
        return Image.new("RGB", (150, 180), "gray")

def verificar_login(login, senha):
    global usuario_logado, tipo_usuario, label_resultado
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    if not login or not senha:
        label_resultado.configure(text="Senha ou Login incorreto", text_color="red")
        return
    
    cursor.execute("SELECT id, senha, tipo FROM usuarios WHERE login = ?", (login,))
    usuario = cursor.fetchone()
    print(usuario)
    conn.close()
    
    if usuario:
        usuario_id, senha_hash, tipo = usuario
        if verificar_senha(senha, senha_hash):
            return usuario_id, tipo
    return None




def cadastrar_usuario(nome, senha, tipo="user"):
    global label_resultado

    if not nome or not senha:
        label_resultado.configure(text="Preencha todos os campos!", text_color="red")
        return
    
    if len(nome) < 4:
        label_resultado.configure(text="Login deve ter pelo menos 4 caracteres", text_color="red")
        return
    if len(senha) < 4:
        label_resultado.configure(text="Senha deve ter pelo menos 4 caracteres", text_color="red")
        return
    
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM usuarios WHERE login = ?", (nome,))
    if cursor.fetchone():
        print("Usuario ja existe")
        conn.close()
        return
    
    senha_hash = gerar_hash(senha)
    
    cursor.execute("INSERT INTO usuarios (login, senha, tipo) VALUES (? ,?, ?)",(nome, senha_hash, tipo))
    
    conn.commit()
    conn.close()
    label_resultado.configure(text="Conta criada com sucesso!", text_color="green")
    print("Usuario cadastrado")    
        
        

#---------------------------------------------------------------------------------------------------------
def nome_usuario(id_usuario):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT login FROM usuarios WHERE id=?", (id_usuario,))
    resultado = cursor.fetchone()
    
    conn.close()
    return resultado[0] if resultado else "Usuário"

#---------------------------------------------------------------------------------------------------------
#Buscar o livro no banco de dados
def buscar_livros():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, capa, quantidade FROM livros")
    livros = cursor.fetchall()
    
    id = id_livro = None
    conn.close()
    return livros 
#-------------------------------------------------------------------
def livro_disponivel(id_livro):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT quantidade FROM livros WHERE id = ?", (id_livro,))
    resultado = cursor.fetchone()
    
    conn.close()
    return resultado and resultado[0] > 0

#---------------------------------------------------------------------------------------------------------

#alugar livro
def alugar_livro(usuario_id, livro_id):
    # if not livro_disponivel(livro_id):
    #     print("Livro indisponível para aluguel.")
    #     return
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    #Data
    data_aluguel = datetime.datetime.now()
    data_devolucao = data_aluguel + datetime.timedelta(days=3)
    
    data_aluguel_str = data_aluguel.strftime("%d/%m/%Y %H:%M")
    data_devolucao_str = data_devolucao.strftime("%d/%m/%Y %H:%M")
    
    cursor.execute("SELECT quantidade FROM livros WHERE id = ?", (livro_id,))
    resultado = cursor.fetchall()
    if resultado is None:
        print("Nao encontrado")
        return
    qtd = resultado [0]
    
    if qtd == 0:
        print("Sem estoque")
        return
    
    
    cursor.execute("UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?", (livro_id,))
    
   
    cursor.execute("INSERT INTO alugueis (usuario_id, livro_id, data_aluguel, data_devolucao, devolvido) VALUES (?, ?, ?, ?, 0)", (usuario_id, livro_id, data_aluguel_str, data_devolucao_str))
    
    #cursor.execute("UPDATE livros SET quantidade = 0 WHERE id = ?", (livro_id,))
    
    
    conn.commit()
    conn.close()
    
    print("Livro alugado com sucesso!")
    tela_livros()

#---------------------------------------------------------------------------------------------------------
#ver os livros alugados
def ver_meus_livros(usuario_id):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT l.id, l.nome, l.capa, a.data_devolucao FROM alugueis a JOIN livros l ON a.livro_id = l.id  WHERE a.usuario_id = ? AND a.devolvido = 0 ", (usuario_id,))
    dados = cursor.fetchall()
    conn.close()
    
    return dados

#devolver livro
def devolver_livro(usuario_id, livro_id):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    
    cursor.execute("SELECT id FROM alugueis WHERE usuario_id = ? AND livro_id = ? AND devolvido = 0 LIMIT 1", (usuario_id, livro_id))
    registro = cursor.fetchall()
    if not registro:
        print("Nenhum livro para devolver")
        return
    aluguel_id = registro[0]
    
    cursor.execute("UPDATE alugueis SET devolvido = 1 WHERE id = ?", (aluguel_id))

        
        
    cursor.execute("UPDATE livros SET quantidade = quantidade + 1 WHERE id = ?", (livro_id,))
    
    #meus_livros = cursor.fetchall()
    conn.commit()
    conn.close()
    
    print("livro devolvido com sucesso!")
    
    tela_meus_livros()
    return #meus_livros

    print("livro devolvido com sucesso!")


def salvar_livro(nome, capa, quantidade):
    if not nome or not capa or not quantidade:
        print("Preencha tudo!")
        return
    try:
        quantidade = int(quantidade)
    except:
        print("Quantidade invalida")
        return
    
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    #for i in range(quantidade):
    cursor.execute("INSERT INTO livros (nome, capa, quantidade) VALUES (?, ?, ?)", (nome, capa, quantidade))
        
    conn.commit()
    conn.close()
    print("Livro adicionado com sucesso!")
    tela_menu()

#-------------------------------------------------------------------------------------
def remover_livro(livro_id):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT quantidade FROM livros WHERE id = ?", (livro_id,))
    resultado = cursor.fetchone()
    
    if not resultado:
        print("Livro nao encontrado")
        return
    quantidade = resultado[0]
    
    if quantidade > 1:
        cursor.execute("UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?",(livro_id,))
    else:
        cursor.execute("DELETE FROM livros WHERE id = ?",(livro_id,))
      
    cursor.execute("SELECT COUNT(*) FROM alugueis WHERE livro_id = ? AND devolvido = 0",(livro_id,))
    em_uso = cursor.fetchone()[0] if resultado else 0
    
    if em_uso > 0:
        print("Nao pode ser removido, livro alugado")
        return
    
      
    conn.commit()
    conn.close()
    print("livro removido!")
    tela_deletar_livros()
#---------------------------------------------------------------------------------------------------------
#login
def fazer_login(login, senha):
    global usuario_logado
    global tipo_usuario
    # login = entry_login.get()
    # senha = entry_senha.get()
    
    usuario = verificar_login(login, senha)
    
    if usuario:
        usuario_logado = usuario[0]
        tipo_usuario = usuario[1]
        print("login ok")
        tela_menu()
    else:
        label_resultado.configure(text="login falhou!", text_color="red")
    

def tela_de_cadastro():
    for widget in app.winfo_children():
        widget.destroy()
    
    global label_resultado
    titulo = ctk.CTkLabel(app, text="Cadastro", font=("Arial", 20))
    titulo.pack(pady=20)
    
    entry_new_nome = ctk.CTkEntry(app, placeholder_text="Usuario")
    entry_new_nome.pack(pady=10)
    
    entry_new_senha = ctk.CTkEntry(app, placeholder_text="Senha", show="*")
    entry_new_senha.pack(pady=10)
    
    tipo_var = ctk.StringVar(value="user")
    
    botao = ctk.CTkButton(app, text="Cadastrar", command=lambda: cadastrar_usuario(entry_new_nome.get(), entry_new_senha.get()))
    botao.pack(pady=10)
    
    botao_voltar = ctk.CTkButton(app, text="Voltar", command=tela_login)
    botao_voltar.pack(pady=10)
    
    label_resultado = ctk.CTkLabel(app, text="")
    label_resultado.pack(pady=10)

        
 #---------------------------------------------------------------------------------------------------------       

def remover_livro(id_livro):
    if tipo_usuario != "admin":
        print("Acesso negado!")
        return

#-------------------------------------------------------------------------------
#Tela do menu      
def tela_menu(): 
    for widget in app.winfo_children():
        widget.destroy()
     
    ADMIN = "admin"
    USER = "user"
        
        
    nome = nome_usuario(usuario_logado)
    titulo_menu = ctk.CTkLabel(app, text=f"Bem-vindo {nome.capitalize()} ao menu !", font=("Arial", 20))
    titulo_menu.pack(pady=20)
    
        
    botao_alugar = ctk.CTkButton(app, text="Alugar livro", command=tela_livros)
    botao_alugar.pack(pady=10)
    
    botao_devolver = ctk.CTkButton(app, text="Devolver livro", command=tela_meus_livros)
    botao_devolver.pack(pady=10)
    
    
    if tipo_usuario == "admin":
        botao_add = ctk.CTkButton(app, text="Adicionar livro", command=tela_adicionar_livro)
        botao_add.pack(pady=10)

        botao_del = ctk.CTkButton(app, text="Remover livro", command=tela_deletar_livros)
        botao_del.pack(pady=10)
    
    botao_login = ctk.CTkButton(app, text="Trocar Usuario", command=tela_login)
    botao_login.pack(pady=10)
    
    botao_sair = ctk.CTkButton(app, text="Sair", command=app.destroy)
    botao_sair.pack(pady=10)

#---------------------------------------------------------------------------------------------------------   
#tela dos livros 

def tela_livros():
    
    for widget in app.winfo_children():
        widget.destroy()
       
    livros = buscar_livros()
    
    botao_voltar = ctk.CTkButton(app, text="Voltar", command=tela_menu)
    botao_voltar.pack(anchor="nw", pady=10, padx=10)
    
    frame = ctk.CTkScrollableFrame(app, width=800, height=600)
    frame.pack(pady=20)
    
    # topo =ctk.CTkFrame(app)
    # topo.pack(fill="x")
    
    # botao_voltar = ctk.CTkButton(app, text="Voltar", command=tela_menu)
    # botao_voltar.pack(side="left", pady=10, padx=10)
    
    coluna = 0
    linha = 0
    
    for id_livro, nome, capa, quantidade in livros:
        
        
        container = ctk.CTkFrame(frame)
        container.grid(row=linha, column=coluna, padx=10, pady=10, sticky="n")
        
        
        nome_livro = ctk.CTkLabel(container, text=f"{nome}", font=("Arial", 16))
        nome_livro.pack(pady=5)
        
        img = ctk.CTkImage(
            light_image=carregar_imagem_url(capa),
            size=(150, 180)
        )
        
        label_img = ctk.CTkLabel(container, image=img, text="")
        label_img.image = img
        label_img.pack(pady=10)
        
        label_qtd = ctk.CTkLabel(container, text=f"Disponivel: {quantidade}", font=("Arial", 14))
        label_qtd.pack()

        if quantidade > 0:

            botao_alugar = ctk.CTkButton(
                container,
                text="Alugar",
                command=lambda id_livro=id_livro: alugar_livro(usuario_logado, id_livro)
            )
            botao_alugar.pack(pady=5)
        else:
            botao_alugar = ctk.CTkButton(container, text="Indisponivel", state="disabled", fg_color="gray")
            botao_alugar.pack(pady=5)

        
    
        coluna += 1
        if coluna >= 4:
            coluna = 0
            linha += 1
        
        #print("livro alugado!")
        #tela_menu()
#---------------------------------------------------------------------------------------------

def tela_meus_livros():
    for widget in app.winfo_children():
        widget.destroy()
        

    botao_voltar = ctk.CTkButton(app, text="Voltar", command=tela_menu)
    botao_voltar.pack(anchor="nw", pady=10, padx=10)
    
    titulo = ctk.CTkLabel(app, text="Meus livros alugados", font=("Arial", 20))
    titulo.pack(pady=20)
    
    livros = ver_meus_livros(usuario_logado)
    
    frame = ctk.CTkScrollableFrame(app, width=800, height=600)
    frame.pack(pady=20)
    
    
    if not livros:
        vazio = ctk.CTkLabel(frame, text="Voce nao tem livro alugado", font=("Arial", 16))
        vazio.pack(pady=20)
        return
    
    coluna = 0
    linha = 0
    
    for id_livro, nome, capa, data_devolucao_str in livros:
        container = ctk.CTkFrame(frame)
        container.grid(row=linha, column=coluna, padx=5, pady=5)
        
        
        nome_label = ctk.CTkLabel(container, text=f"{nome}", font=("Arial", 16))
        nome_label.pack(padx=10)
        
        label = ctk.CTkLabel(container, text=f"Devolver ate: {data_devolucao_str}", font=("Arial", 16))
        label.pack()
        
        
        
        img = ctk.CTkImage(
            light_image=carregar_imagem_url(capa),
            size=(150, 180)
        )
        
        label_img = ctk.CTkLabel(container, image=img, text="")
        label_img.image = img
        label_img.pack(pady=10)
        

        
        botao_devolver = ctk.CTkButton(container, text="Devolver", command=lambda id_livro=id_livro: devolver_livro(usuario_logado, id_livro))
        botao_devolver.pack(side="right", padx=50)

        
        coluna += 1
        if coluna >= 3:
            coluna = 0
            linha += 1

def tela_adicionar_livro():
    for widget in app.winfo_children():
        widget.destroy()
        
    ctk.CTkLabel(app, text="Adicionar livro", font=("Arial", 20)).pack(pady=20)
    
    entry_nome = ctk.CTkEntry(app, placeholder_text="Nome do livro")
    entry_nome.pack(pady=10)

    entry_capa = ctk.CTkEntry(app, placeholder_text="Add Capa")
    entry_capa.pack(pady=10)
    
    entryqtd = ctk.CTkEntry(app, placeholder_text="Quantidade")
    entryqtd.pack(pady=10)
    
    ctk.CTkButton(app, text="Salvar", command=lambda: salvar_livro(entry_nome.get(), entry_capa.get(), entryqtd.get())).pack(pady=10)
    
    ctk.CTkButton(app, text="Voltar", command=tela_menu).pack(pady=10)


def confirmar_remover(id_livro):
    if messagebox.askyesno("Confirmação", "Deseja deletar esse livro?"):
        remover_livro(id_livro)
        tela_deletar_livros


def tela_deletar_livros():
    for widget in app.winfo_children():
        widget.destroy()
        
    titulo = ctk.CTkLabel(app, text="Deletar livros", font=("Arial", 20))
    titulo.pack(pady=20)
    
    botao_voltar = ctk.CTkButton(app, text="Voltar", command=tela_menu)
    botao_voltar.pack(anchor="nw", padx=10, pady=10)
    
    livros = buscar_livros()
    
    frame = ctk.CTkScrollableFrame(app, width=800, height=600)
    frame.pack(pady=10)
    
    coluna = 0
    linha = 0
    
    for id_livro, nome, capa, quantidade in livros:
        
        container = ctk.CTkFrame(frame)
        container.grid(row=linha, column=coluna, padx=10, pady=10)
        
        nome_label = ctk.CTkLabel(container, text=nome, font=("Arial", 16))
        nome_label.pack(pady=5)
        
        img = ctk.CTkImage(light_image=carregar_imagem_url(capa), size=(150, 180))
        
        label_img = ctk.CTkLabel(container, image=img, text="")
        label_img.image = img
        label_img.pack(pady=5)
        
        qtd_label = ctk.CTkLabel(container, text=f"Quantidade: {quantidade}")
        qtd_label.pack()
        
        botao_deletar = ctk.CTkButton(container, text="Deletar", fg_color="red", command=lambda id_livro=id_livro: confirmar_remover(id_livro))
        botao_deletar.pack(pady=5)        

        coluna += 1
        if coluna >= 4:
            coluna = 0
            linha += 1
            

def tela_login():
    for widget in app.winfo_children():
        widget.destroy()
    global label_resultado   
    titulo = ctk.CTkLabel(app, text="Faça seu login", font=("Arial", 20))
    titulo.pack(pady=20)
    
    entry_login = ctk.CTkEntry(app, placeholder_text="login")
    entry_login.pack(pady=10)
    
    entry_senha = ctk.CTkEntry(app, placeholder_text="senha", show="*")
    entry_senha.pack(pady=10)
    
    botao_login = ctk.CTkButton(app, text="login", command=lambda: fazer_login(entry_login.get(), entry_senha.get()))
    botao_login.pack(pady=10)
    
    botao_cadastrar = ctk.CTkButton(app, text="Cadastrar", command=tela_de_cadastro)
    botao_cadastrar.pack(pady=10)
    
    botao_sair = ctk.CTkButton(app, text="Sair", command=app.destroy)
    botao_sair.pack(pady=10)
    
    
    label_resultado = ctk.CTkLabel(app, text="")
    label_resultado.pack(pady=10)


app = ctk.CTk()
app.title("Locadora de livros")
app.geometry("800x600")

titulo = ctk.CTkLabel(app, text="Bem vindo a Blibioteca", font=("Arial", 20))
titulo.pack(pady=20)


botao_login = ctk.CTkButton(app, text="login", command=tela_login)
botao_login.pack(pady=10)

botao_cadastrar = ctk.CTkButton(app, text="Cadastrar", command=tela_de_cadastro)
botao_cadastrar.pack(pady=10)

botao_sair = ctk.CTkButton(app, text="Sair", command=app.destroy)
botao_sair.pack(pady=10)


label_resultado = ctk.CTkLabel(app, text="")
label_resultado.pack(pady=10)


app.mainloop()