"""Serviço de envio de notificações via Telegram"""
import httpx
import logging
from typing import Optional


class NotificationService:
    """Serviço de envio de notificações"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializa o serviço de notificação.
        
        Args:
            bot_token: Token do bot do Telegram
            chat_id: ID do chat para enviar mensagens
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
    
    def send_new_low_alert(
        self,
        route,
        current_price: float,
        historical_low: Optional[float],
        offer_details: dict,
    ) -> bool:
        """
        Envia alerta de novo menor preço via Telegram.
        
        Args:
            route: RouteWatch que gerou o alerta
            current_price: Preço atual
            historical_low: Menor preço anterior
            offer_details: Detalhes da oferta
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        message = self._format_alert_message(route, current_price, historical_low, offer_details)
        
        try:
            response = httpx.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            self.logger.info(f"Alerta enviado via Telegram para RouteWatch {route.id}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta via Telegram: {e}", exc_info=True)
            return False
    
    def _format_alert_message(
        self,
        route,
        current_price: float,
        historical_low: Optional[float],
        offer_details: dict,
    ) -> str:
        """
        Formata mensagem de alerta.
        
        Args:
            route: RouteWatch
            current_price: Preço atual
            historical_low: Menor preço anterior
            offer_details: Detalhes da oferta
            
        Returns:
            Mensagem formatada em HTML
        """
        previous_text = f"{historical_low:.2f}" if historical_low else "N/A"
        
        message = f"""🔥 <b>Novo menor preço histórico!</b>

<b>Rota:</b> {route.origin} → {route.destination}
<b>Ida:</b> {route.departure_date.strftime('%d/%m/%Y')}
<b>Volta:</b> {route.return_date.strftime('%d/%m/%Y')}

<b>Companhia:</b> {offer_details['airline']}
<b>Preço atual:</b> {route.currency} {current_price:.2f}
<b>Menor anterior:</b> {route.currency} {previous_text}
<b>Escalas:</b> {offer_details['stops']}

<b>Saída:</b> {offer_details['departure_at']}
<b>Retorno:</b> {offer_details['return_at']}

<i>Fonte: SerpApi / Google Flights</i>
"""
        return message
