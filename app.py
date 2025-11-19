from flask import Flask, render_template_string, redirect, request, session
from refeitorio import (
    listar_refeicoes,
    listar_pessoas,
    init_db,
    autenticar_usuario,
    criar_usuario_sistema,
)
from eventos import processar_evento

app = Flask(__name__)
app.secret_key = "uma_chave_secreta_bem_difícil_aqui"  # depois você troca


# ---------- HTMLs básicos ----------

LOGIN_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Login</title></head>
<body style="font-family: Arial; padding: 20px;">
  <h2>Login</h2>
  <form method="post">
    Email:<br><input name="email"><br><br>
    Senha:<br><input type="password" name="senha"><br><br>
    <button type="submit">Entrar</button>
  </form>
  {% if erro %}
    <p style="color:red">{{ erro }}</p>
  {% endif %}
</body>
</html>
"""

REGISTER_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Criar admin</title></head>
<body style="font-family: Arial; padding: 20px;">
  <h2>Criar usuário administrador</h2>
  <form method="post">
    Nome:<br><input name="nome"><br><br>
    Email:<br><input name="email"><br><br>
    Senha:<br><input type="password" name="senha"><br><br>
    <button type="submit">Criar</button>
  </form>
</body>
</html>
"""

HOME_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Painel de Refeitório</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #f2f2f2; }
    .topbar { margin-bottom: 15px; }
    .btn { padding: 6px 10px; background: #007bff; color: #fff;
           text-decoration: none; border-radius: 4px; }
    .btn:hover { background: #0056b3; }
  </style>
</head>
<body>

  <div class="topbar">
    Logado como: {{ user_nome }} |
    <a href="/logout">Sair</a>
  </div>

  <h1>Pessoas cadastradas</h1>
  <table>
    <thead>
      <tr><th>ID</th><th>Nome</th><th>Matrícula</th><th>Ação</th></tr>
    </thead>
    <tbody>
    {% for p in pessoas %}
      <tr>
        <td>{{ p[0] }}</td>
        <td>{{ p[1] }}</td>
        <td>{{ p[2] }}</td>
        <td><a class="btn" href="/registrar/{{ p[0] }}">Registrar refeição</a></td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

  <h1>Refeições registradas</h1>
  <table>
    <thead>
      <tr><th>ID</th><th>Pessoa</th><th>Data</th><th>Hora</th><th>Tipo</th></tr>
    </thead>
    <tbody>
    {% for r in refeicoes %}
      <tr>
        <td>{{ r[0] }}</td>
        <td>{{ r[1] }}</td>
        <td>{{ r[2] }}</td>
        <td>{{ r[3] }}</td>
        <td>{{ r[4] }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

</body>
</html>
"""


# ---------- Proteção das rotas ----------

@app.before_request
def exigir_login():
    rota = request.path
    # libera login e criação do admin
    if rota.startswith("/login") or rota.startswith("/register_admin"):
        return
    # tudo o resto exige usuário logado
    if "user_id" not in session:
        return redirect("/login")


# ---------- Rotas de autenticação ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    init_db()
    erro = None
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        user = autenticar_usuario(email, senha)
        if user:
            session["user_id"] = user[0]
            session["user_nome"] = user[1]
            return redirect("/")
        else:
            erro = "Usuário ou senha inválidos."
    return render_template_string(LOGIN_HTML, erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/register_admin", methods=["GET", "POST"])
def register_admin():
    init_db()
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        criar_usuario_sistema(nome, email, senha)
        return redirect("/login")
    return render_template_string(REGISTER_HTML)


# ---------- Rotas principais ----------

@app.route("/")
def home():
    init_db()
    return render_template_string(
        HOME_HTML,
        pessoas=listar_pessoas(),
        refeicoes=listar_refeicoes(),
        user_nome=session.get("user_nome"),
    )


@app.route("/registrar/<int:pessoa_id>")
def registrar(pessoa_id):
    processar_evento(pessoa_id)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

