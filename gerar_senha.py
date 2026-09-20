"""Gera o hash de uma senha para colocar no dicionário USUARIOS em app3.py.

Uso:
    python gerar_senha.py "senha-da-pessoa"

Copie a saída e cole em app3.py, por exemplo:
    USUARIOS = {
        "rafael": "<hash gerado aqui>",
        "novo-usuario": "<outro hash>",
    }
"""
import sys

from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Uso: python gerar_senha.py "senha-da-pessoa"')
        sys.exit(1)
    print(generate_password_hash(sys.argv[1]))
