import os
import base64
from datetime import datetime

from flask import Flask, render_template_string, redirect, request, session
from refeitorio import (
    listar_refeicoes,
    listar_pessoas,
    init_db,
    autenticar_usuario,
    criar_usuario_sistema,
    cadastrar_pessoa,
)
from eventos import processar_evento

app = Flask(__name__)
app.secret_key = "uma_chave_secreta_bem_difícil_aqui"  # TROCAR DEPOIS


# ---------- HTMLs ----------

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
    <a href="/logout">Sair</a> |
    <a class="btn" href="/cadastrar_facial">Cadastrar facial</a>
  </div>

  <h1>Pessoas cadastradas</h1>
  <table>
    <thead>
      <tr><th>ID</th><th>Nome</th><th>Matrícula</th><th>Foto</th><th>Ação</th></tr>
    </thead>
    <tbody>
    {% for p in pessoas %}
      <tr>
        <td>{{ p[0] }}</td>
        <td>{{ p[1] }}</td>
        <td>{{ p[2] }}</td>
        <td>
          {% if p[3] %}
            <img src="/static/{{ p[3] }}" alt="foto" style="height:60px;">
          {% else %}
            -
          {% endif %}
        </td>
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

FACIAL_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Cadastrar facial</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    video { width: 100%; max-width: 400px; border: 1px solid #ccc; }
    input { padding: 6px; width: 100%; max-width: 400px; margin-bottom: 10px; }
    button { padding: 8px 16px; }
  </style>
</head>
<body>
  <h2>Cadastrar funcionário com facial</h2>

  <label>Nome:</label><br>
  <input id="nome"><br>
  <label>Matrícula (opcional):</label><br>
  <input id="matricula"><br>

  <p><b>Câmera:</b></p>
  <video id="video" autoplay playsinline></video>
  <canvas id="canvas" style="display:none;"></canvas>

  <br><br>
  <button onclick="capturar()">Capturar foto e salvar</button>
  <p id="msg"></p>

  <script>
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const msg = document.getElementById('msg');

    // Ativa a câmera
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => { video.srcObject = stream; })
      .catch(err => { msg.textContent = 'Erro ao acessar câmera: ' + err; });

    function capturar() {
      const nome = document.getElementById('nome').value.trim();
      const matricula = document.getElementById('matricula').value.trim();

      if (!nome) {
        alert('Preencha o nome');
        return;
      }

      const w = video.videoWidth;
      const h = video.videoHeight;
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, w, h);

      const dataUrl = canvas.toDataURL('image/png');

      msg.textContent = 'Enviando...';

      fetch('/cadastrar_facial', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          nome: nome,
          matricula: matricula,
          imagem: dataUrl
        })
      })
      .then(r => r.json())
      .then(r => {
        if (r.ok) {
          msg.textContent = 'Cadastrado com sucesso!';
          setTimeout(() => { window.location = '/'; }, 1000);
        } else {
          msg.textContent = 'Erro: ' + (r.error || 'desconhecido');
        }
      })
      .catch(err => {
        msg.textContent = 'Erro de rede: ' + err;
      });
    }
  </script>
</body>
</html>
"""


# ---------- Proteção de rotas ----------

@app.before_request
def exigir_login():
    rota = request.path
    if rota.startswith("/login") or rota.startswith("/register_admin") or rota.startswith("/static/"):
        return
    if "user_id" not in session:
        return redirect("/login")


# ---------- Login ----------

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


# ---------- Cadastro facial ----------

@app.route("/cadastrar_facial", methods=["GET", "POST"])
def cadastrar_facial():
    init_db()
    if request.method == "GET":
        return render_template_string(FACIAL_HTML)

    data = request.get_json()
    nome = data.get("nome")
    matricula = data.get("matricula") or ""
    imagem = data.get("imagem")

    if not nome or not imagem:
        return {"ok": False, "error": "Dados incompletos"}, 400

    # imagem vem no formato data:image/png;base64,AAAA...
    try:
        header, b64 = imagem.split(",", 1)
    except ValueError:
        return {"ok": False, "error": "Formato de imagem inválido"}, 400

    img_bytes = base64.b64decode(b64)

    os.makedirs("static/faces", exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d%H%M%S%f") + ".png"
    rel_path = f"faces/{filename}"
    full_path = os.path.join("static", "faces", filename)

    with open(full_path, "wb") as f:
        f.write(img_bytes)

    cadastrar_pessoa(nome, matricula, rel_path)

    return {"ok": True}


if __name__ == "__main__":
    app.run(debug=True)
