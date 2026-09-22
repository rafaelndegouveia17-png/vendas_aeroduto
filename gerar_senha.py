"""Gera o hash de uma senha para colocar no dicionário USUARIOS em app3.py.

Uso:
    python gerar_senha.py "senha-da-pessoa"

Copie a saída para dentro do dicionário, escolhendo o papel
("admin" pode editar, "usuario" só visualiza):
    USUARIOS = {
        "rafael": {"senha": "<hash gerado aqui>", "papel": "admin"},
        "novo-usuario": {"senha": "<outro hash>", "papel": "usuario"},
    }
"""
import sys

from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Uso: python gerar_senha.py "senha-da-pessoa"')
        sys.exit(1)
    print(generate_password_hash(sys.argv[1]))
