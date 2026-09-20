"""Camada de acesso a dados (Firestore) para o Vendas Aeroduto.

Isolar aqui o acesso ao Firestore permite trocar o cliente real por um
falso nos testes, sem precisar de credenciais de verdade.
"""

NOMES_PADRAO = ["Equipe A", "Equipe B", "Equipe C"]


def id_do_mes(ano, mes):
    return f"{ano:04d}-{mes:02d}"


def mes_padrao():
    return {
        "meta": 0,
        "gauges": [{"nome": nome, "entradas": []} for nome in NOMES_PADRAO],
    }


class Armazenamento:
    """Wrapper fino sobre um cliente Firestore (real ou falso)."""

    def __init__(self, db):
        self.db = db

    def obter_mes(self, ano, mes):
        doc = self.db.collection("meses").document(id_do_mes(ano, mes)).get()
        if doc.exists:
            dados = doc.to_dict()
            dados.setdefault("meta", 0)
            dados.setdefault("gauges", mes_padrao()["gauges"])
            # garante sempre 3 gauges mesmo se o documento estiver incompleto
            while len(dados["gauges"]) < 3:
                dados["gauges"].append(
                    {"nome": NOMES_PADRAO[len(dados["gauges"])], "entradas": []}
                )
            return dados
        return mes_padrao()

    def salvar_mes(self, ano, mes, dados):
        self.db.collection("meses").document(id_do_mes(ano, mes)).set(dados)

    def definir_meta_mes(self, ano, mes, nova_meta):
        dados = self.obter_mes(ano, mes)
        dados["meta"] = nova_meta
        self.salvar_mes(ano, mes, dados)
        return dados

    def definir_nome_velocimetro(self, ano, mes, indice, nome):
        dados = self.obter_mes(ano, mes)
        dados["gauges"][indice]["nome"] = nome
        self.salvar_mes(ano, mes, dados)
        return dados

    def adicionar_entrada(self, ano, mes, indice, cliente, valor):
        dados = self.obter_mes(ano, mes)
        dados["gauges"][indice]["entradas"].append({"cliente": cliente, "valor": valor})
        self.salvar_mes(ano, mes, dados)
        return dados

    def remover_entrada(self, ano, mes, indice, indice_entrada):
        dados = self.obter_mes(ano, mes)
        dados["gauges"][indice]["entradas"].pop(indice_entrada)
        self.salvar_mes(ano, mes, dados)
        return dados

    def obter_meta_ano_override(self, ano):
        doc = self.db.collection("anos").document(str(ano)).get()
        if doc.exists:
            dados = doc.to_dict()
            return dados.get("meta")
        return None

    def definir_meta_ano(self, ano, meta):
        self.db.collection("anos").document(str(ano)).set({"meta": meta})

    @staticmethod
    def calcular_totais_mes(dados):
        atuais_gauges = [sum(e["valor"] for e in g["entradas"]) for g in dados["gauges"]]
        atual_mes = sum(atuais_gauges)
        return atual_mes, atuais_gauges

    def detalhar_ano(self, ano):
        """Retorna (meta_ano, atual_ano, concluido_ano, detalhes_por_mes).

        meta_ano é a meta definida manualmente para o ano (definir_meta_ano),
        ou, se nenhuma foi definida ainda, a soma automática das metas dos 12 meses.
        """
        meta_override = self.obter_meta_ano_override(ano)
        detalhes = []
        soma_metas = 0
        soma_atual = 0
        for mes in range(1, 13):
            dados = self.obter_mes(ano, mes)
            atual_mes, _ = self.calcular_totais_mes(dados)
            detalhes.append({"mes": mes, "meta": dados["meta"], "atual": atual_mes})
            soma_metas += dados["meta"]
            soma_atual += atual_mes

        meta_ano = meta_override if meta_override is not None else soma_metas
        concluido_ano = "sim" if meta_ano > 0 and soma_atual >= meta_ano else "não"
        return meta_ano, soma_atual, concluido_ano, detalhes


def estado_completo(armazenamento, ano, mes):
    """Monta o JSON completo (mês selecionado + acumulado do ano) que o front-end consome."""
    dados = armazenamento.obter_mes(ano, mes)
    atual_mes, atuais_gauges = armazenamento.calcular_totais_mes(dados)
    meta_mes = dados["meta"]
    concluido_mes = "sim" if meta_mes > 0 and atual_mes >= meta_mes else "não"

    meta_ano, atual_ano, concluido_ano, meses_do_ano = armazenamento.detalhar_ano(ano)

    return {
        "ano": ano,
        "mes": mes,
        "meta_mes": meta_mes,
        "atual_mes": atual_mes,
        "concluido_mes": concluido_mes,
        "velocimetros": [
            {"nome": g["nome"], "atual": atuais_gauges[i], "entradas": g["entradas"]}
            for i, g in enumerate(dados["gauges"])
        ],
        "meta_ano": meta_ano,
        "atual_ano": atual_ano,
        "concluido_ano": concluido_ano,
        "meses_do_ano": meses_do_ano,
    }