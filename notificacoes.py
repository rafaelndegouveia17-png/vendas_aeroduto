"""Envio de notificação (SMS ou WhatsApp) quando uma entrada nova é adicionada.

Usa o Twilio. Falhas de envio nunca devem derrubar a operação principal
(adicionar a entrada) -- por isso todo erro aqui é engolido e só vai pro
log do servidor.
"""


class Notificador:
    def __init__(self, cliente, numero_origem, destinatarios, canal="sms"):
        self.cliente = cliente
        self.numero_origem = numero_origem
        self.destinatarios = destinatarios
        self.canal = canal  # "sms" ou "whatsapp"

    @property
    def ativo(self):
        return bool(self.cliente and self.numero_origem and self.destinatarios)

    def notificar_nova_entrada(self, velocimetro_nome, cliente_nome, valor, mes, ano):
        if not self.ativo:
            return

        valor_formatado = f"{valor:,}".replace(",", ".")
        texto = (
            f"Vendas Aeroduto: nova entrada em {velocimetro_nome} "
            f"({mes:02d}/{ano}) - {cliente_nome}: R$ {valor_formatado}"
        )

        for destino in self.destinatarios:
            try:
                self._enviar_uma(texto, destino)
            except Exception as erro:  # nunca deixa a notificação quebrar o fluxo principal
                print(f"[notificacoes] falha ao enviar para {destino}: {erro}")

    def _enviar_uma(self, texto, destino):
        de = self._formatar_numero(self.numero_origem)
        para = self._formatar_numero(destino)
        self.cliente.messages.create(body=texto, from_=de, to=para)

    def _formatar_numero(self, numero):
        if self.canal == "whatsapp" and not numero.startswith("whatsapp:"):
            return f"whatsapp:{numero}"
        return numero
