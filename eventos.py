from datetime import datetime
from refeitorio import registrar_refeicao, cadastrar_pessoa, init_db

def processar_evento(user_id, timestamp=None):
    """
    Simula a chegada de um evento da máquina facial.
    user_id = id da pessoa no banco
    timestamp = horário do reconhecimento
    """

    if timestamp is None:
        timestamp = datetime.now()

    print(f"\n➡ Evento recebido: usuário {user_id} às {timestamp}")

    sucesso = registrar_refeicao(user_id, dt=timestamp)

    if sucesso:
        print("🍽️ Refeição registrada com sucesso!")
    else:
        print("⚠️ Essa pessoa já comeu hoje! Refeição NÃO registrada.")

    return sucesso


if __name__ == "__main__":
    # Inicializa o banco (apaga nada, só garante que existe)
    init_db()

    # CADASTRAR DUAS PESSOAS SÓ PARA TESTE
    id_joao = cadastrar_pessoa("João da Silva", "001")
    id_maria = cadastrar_pessoa("Maria Souza", "002")

    # SIMULANDO EVENTOS DA MÁQUINA
    processar_evento(id_joao)     # Primeira refeição: deve registrar
    processar_evento(id_joao)     # Segunda refeição: deve bloquear
    processar_evento(id_maria)    # Deve registrar normalmente
