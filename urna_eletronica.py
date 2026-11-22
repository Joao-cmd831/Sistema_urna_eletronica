import sqlite3
from pathlib import Path

# Configurções
DB_PATH = Path(__file__).with_name("urna_eletronica.db")
MINIMO_VOTOS = 10


# Conexão com o banco
def conectar():
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute("pragma foreign_keys = on")
    return conexao


# Criação das tabelas
def criar_banco():
    with conectar() as conexao:

        conexao.execute("""
            create table if not exists candidatos (
                id integer primary key autoincrement,
                numero integer not null unique,
                nome text not null,
                partido text not null
            )
        """)

        conexao.execute("""
            create table if not exists eleitores (
                id integer primary key autoincrement,
                identificador text not null unique,
                data_voto text npt null default current_timestamp,
                candidato_id integer not null,
                foreign key (candidato_id) REFERENCES candidatos(id)
            )
        """)

        conexao.commit()


# Cadastro de candidatos
def cadastrar_candidato():
    print("\n=== CADASTRO DE CANDIDATO ===")

    try:
        numero = int(input("Número do candidato: ").strip())
        nome = input("Nome do candidato: ").strip()
        partido = input("Partido: ").strip()

        if not nome or not partido:
            print("Nome e partido são obrigatórios.")
            return

        with conectar() as conexao:
            conexao.execute(
                """
                insert into candidatos (numero, nome, partido)
                values (?, ?, ?)
                """,
                (numero, nome, partido)
            )

        print("Candidato cadastrado com sucesso!")

    except ValueError:
        print("Digite um número válido para o candidato.")

    except sqlite3.IntegrityError:
        print("Esse número já está cadastrado.")


# Listagem de candidatos
def listar_candidatos():
    with conectar() as conexao:
        candidatos = conexao.execute(
            """
            select id, numero, nome, partido
            from candidatos
            order by numero
            """
        ).fetchall()

    print("\n=== CANDIDATOS CADASTRADOS ===")

    if not candidatos:
        print("Nenhum candidato cadastrado.")
    else:
        for _, numero, nome, partido in candidatos:
            print(f"Nº {numero} | {nome} | Partido: {partido}")

    return candidatos


# Registro de votos
def votar():
    print("\n=== ÁREA DE VOTAÇÃO ===")

    identificador = input(
        "Identificação do eleitor (ex.: matrícula ou código): "
    ).strip()

    if not identificador:
        print("A identificação não pode ficar vazia.")
        return

    with conectar() as conexao:

        ja_votou = conexao.execute(
    "Select 1 from eleitores where identificador = ?",
    (identificador,)
    ).fetchone()

        if ja_votou:
            print("VOTO NÃO REGISTRADO: este eleitor já votou.")
            return

        candidatos = conexao.execute(
            """
            select id, numero, nome, partido
            from candidatos
            order by numero
            """
        ).fetchall()

        if not candidatos:
            print("Cadastre pelo menos um candidato antes da votação.")
            return

        print("\nCandidatos disponíveis:")

        for _, numero, nome, partido in candidatos:
            print(f"{numero} - {nome} ({partido})")

        try:
            numero_escolhido = int(
                input("Digite o número do seu candidato: ").strip()
            )

        except ValueError:
            print("Número inválido. Voto não registrado.")
            return

        candidato = conexao.execute(
            """
            SELECT id, nome FROM candidatos
            WHERE numero = ?
            """,
            (numero_escolhido,)
        ).fetchone()

        if candidato is None:
            print("Candidato não encontrado. Voto não registrado.")
            return

        confirmacao = input(
            f"Confirma seu voto em {candidato[1]}? (S/N): "
        ).strip().upper()

        if confirmacao != "S":
            print("Votação cancelada. Nenhum voto foi registrado.")
            return

        try:
            conexao.execute(
                """
                insert into eleitores (identificador, candidato_id)
                values (?, ?)
                """,
                (identificador, candidato[0])
            )

            print("VOTO COMPUTADO COM SUCESSO!")

        except sqlite3.IntegrityError:
            print("Não foi possível registrar o voto.")


# Exibição dos resultados
def mostrar_resultado():
    with conectar() as conexao:

        total = conexao.execute(
            "select count(*) from eleitores"
        ).fetchone()[0]

        resultados = conexao.execute("""
            select
                c.numero,
                c.nome,
                c.partido,
                count(e.id) as votos
            from candidatos c
            left join eleitores e on e.candidato_id = c.id
            group by c.id, c.numero, c.nome, c.partido
            order by votos desc, c.numero
        """).fetchall()

    print("\n=== RESULTADO DA ELEIÇÃO ===")
    print(f"Total de votos registrados: {total}")

    if not resultados:
        print("Não há candidatos cadastrados.")
        return

    for numero, nome, partido, votos in resultados:
        percentual = (votos / total * 100) if total else 0

        print(f"\nNº {numero} | {nome} ({partido})")
        print(f"Votos: {votos} | Percentual: {percentual:.1f}%")
        print("-" * 40)

    maior_votacao = resultados[0][3]

    vencedores = [
        resultado
        for resultado in resultados
        if resultado[3] == maior_votacao
    ]

    if total == 0:
        print("Ainda não há votos para definir um resultado.")

    elif len(vencedores) > 1:
        print("Resultado: empate entre os candidatos acima.")

    else:
        print(f"Mais votado: {vencedores[0][1]}")


# Painel de votação
def painel():
    with conectar() as conexao:

        total = conexao.execute(
            "SELECT COUNT(*) FROM eleitores"
        ).fetchone()[0]

        quantidade = conexao.execute(
            "SELECT COUNT(*) FROM candidatos"
        ).fetchone()[0]

    print("\n=== PAINEL DA URNA ===")
    print(f"Candidatos cadastrados: {quantidade}")
    print(f"Votos computados: {total}")
    print(f"Meta mínima da atividade: {MINIMO_VOTOS} votações")

    if total < MINIMO_VOTOS:
        print(
            f"Faltam {MINIMO_VOTOS - total} voto(s) "
            "para atingir o mínimo."
        )
    else:
        print("Mínimo de 10 votações atingido!")


# Opção de limpar os dados
def limpar_dados():
    print("\n=== LIMPAR DADOS DA URNA ===")

    confirmacao = input(
        "Tem certeza que deseja apagar todos os candidatos e votos? (S/N): "
    ).strip().upper()

    if confirmacao == "S":

        with conectar() as conexao:
            conexao.execute("DELETE FROM eleitores")
            conexao.execute("DELETE FROM candidatos")

        print("Todos os dados foram apagados com sucesso!")

    else:
        print("Operação cancelada.")


# Menu principal
def menu():
    criar_banco()

    while True:
        print("\n========== SISTEMA DE URNA ==========")
        print("1 - Cadastrar candidato")
        print("2 - Listar candidatos")
        print("3 - Registrar voto")
        print("4 - Exibir resultado")
        print("5 - Ver painel da votação")
        print("6 - Limpar todos os dados")
        print("0 - Sair")
        print("=====================================")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_candidato()

        elif opcao == "2":
            listar_candidatos()

        elif opcao == "3":
            votar()

        elif opcao == "4":
            mostrar_resultado()

        elif opcao == "5":
            painel()

        elif opcao == "6":
            limpar_dados()

        elif opcao == "0":
            print("Sistema encerrado. Obrigado!")
            break

        else:
            print("Opção inválida. Tente novamente.")


# Inicialização do programa
if __name__ == "__main__":
    menu()
