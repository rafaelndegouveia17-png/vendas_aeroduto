# Vendas Aeroduto

## O que mudou nesta versão

- Você escolhe **mês e ano** no topo da página.
- **Acumulado do mês** (velocímetro grande, à esquerda): só a **meta** é editável — o valor atual é a soma automática dos 3 velocímetros de clientes.
- **3 velocímetros de clientes** (à direita): você edita o **nome** de cada um e adiciona **entradas** (nome do cliente + valor) — cada entrada soma no total daquele velocímetro. Eles não têm meta própria; a barra deles é desenhada usando a **meta do mês** como escala, para mostrar visualmente quanto cada um contribuiu para a meta.
- **Acumulado do ano** (embaixo): calculado automaticamente como a soma do acumulado dos 12 meses do ano selecionado. A meta anual também é automática (soma das metas dos 12 meses) — não existe mais uma meta anual separada, só a do mês.
- **Login obrigatório**: só quem tiver usuário/senha cadastrados consegue acessar.
- **Firestore (Firebase)** no lugar da memória do Python — os dados agora persistem entre reinícios do servidor.

## 1. Instalar as dependências

```bash
pip install -r requirements.txt
```

## 2. Configurar o Firebase

1. Acesse [console.firebase.google.com](https://console.firebase.google.com) e crie um projeto (ou use um existente).
2. No menu lateral, vá em **Compilação → Firestore Database** e crie o banco (modo produção ou teste, tanto faz para começar).
3. Vá em **Configurações do projeto (engrenagem) → Contas de serviço**.
4. Clique em **Gerar nova chave privada** — isso baixa um arquivo `.json`.
5. Renomeie esse arquivo para `credenciais_firebase.json` e coloque na mesma pasta do `app3.py`.
   - Se preferir outro nome/local, defina a variável de ambiente `FIREBASE_CREDENCIAIS` com o caminho do arquivo.
6. **Nunca** suba esse arquivo para um repositório público — ele dá acesso total ao seu Firestore.

## 3. Configurar quem pode acessar

Abra `app3.py` e edite o dicionário `USUARIOS`. Para gerar o hash de uma senha:

```bash
python gerar_senha.py "senha-da-pessoa"
```

Copie a saída para dentro do dicionário:

```python
USUARIOS = {
    "rafael": "<hash gerado>",
    "outra-pessoa": "<outro hash>",
}
```

## 4. Definir a chave de sessão (recomendado)

Antes de rodar em produção, defina uma chave aleatória:

```bash
export FLASK_SECRET_KEY="qualquer-texto-longo-e-aleatorio"
```

Sem isso, o app usa uma chave fixa de desenvolvimento — funciona, mas não é seguro para produção.

## 5. Rodar

```bash
python app3.py
```

Abra o endereço mostrado no terminal, faça login, e pronto.

## Estrutura de dados no Firestore

Cada mês vira um documento na coleção `meses`, com ID no formato `AAAA-MM` (ex: `2026-03`):

```json
{
  "meta": 100000,
  "gauges": [
    { "nome": "Equipe A", "entradas": [{ "cliente": "Cliente A", "valor": 20000 }] },
    { "nome": "Equipe B", "entradas": [] },
    { "nome": "Equipe C", "entradas": [] }
  ]
}
```

O acumulado do mês, do ano, e as metas de ano são sempre **calculados na hora** a partir desses documentos — nada disso fica salvo separadamente, então não há risco de ficar dessincronizado.
