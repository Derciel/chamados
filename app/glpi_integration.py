# glpi_integration.py

import requests
import json
import logging

# Configuração básica de logging para ajudar a depurar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GLPIIntegration:
    """
    Classe para gerenciar a integração de chamados com a API do GLPI.
    """
    def __init__(self, glpi_url: str, user_token: str, app_token: str):
        """
        Inicializa a classe de integração.

        Args:
            glpi_url (str): A URL base da sua instância do GLPI. Ex: "http://glpi.suaempresa.com"
            user_token (str): O token de usuário gerado no GLPI para autenticação.
            app_token (str): O token de aplicação gerado no GLPI para a API.
        """
        self.base_url = f"{glpi_url}/apirest.php"
        self.user_token = user_token
        self.app_token = app_token
        self.session_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'App-Token': self.app_token
        }

    def authenticate(self) -> bool:
        """
        Autentica na API do GLPI para obter um token de sessão.
        O token de sessão é necessário para todas as outras chamadas à API.
        """
        # Adiciona o token de usuário específico para a autenticação
        auth_headers = self.headers.copy()
        auth_headers['Authorization'] = f'user_token {self.user_token}'
        
        try:
            logging.info("Tentando autenticar no GLPI...")
            response = requests.get(f"{self.base_url}/initSession", headers=auth_headers)
            
            # Lança uma exceção se a resposta for um erro HTTP (4xx ou 5xx)
            response.raise_for_status() 
            
            data = response.json()
            if 'session_token' in data:
                self.session_token = data['session_token']
                # Atualiza o header principal com o token de sessão para futuras requisições
                self.headers['Session-Token'] = self.session_token
                logging.info("Autenticação no GLPI bem-sucedida!")
                return True
            else:
                logging.error(f"Falha na autenticação: {data}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao autenticar no GLPI: {e}")
            return False

    def _map_priority(self, prioridade_local: str) -> int:
        """
        Mapeia a prioridade do sistema local para o valor correspondente no GLPI.
        Ref: Documentação do GLPI sobre os valores de urgência.
        """
        mapping = {
            'Baixa': 2,   # Média no GLPI (padrão)
            'Média': 3,   # Alta no GLPI
            'Alta': 4     # Muito Alta no GLPI
        }
        return mapping.get(prioridade_local, 2) # Retorna 'Média' como padrão

    def _get_entity_id_by_sector(self, setor: str) -> int:
        """
        Mapeia o nome do setor para o ID da entidade correspondente no GLPI.
        Estes IDs devem ser verificados na sua instância do GLPI.
        """
        # IMPORTANTE: Os IDs das entidades podem variar. Verifique em Setup > Entidades no seu GLPI.
        sector_mapping = {
            'TI': 0,           # Exemplo: Entidade Raiz
            'Financeiro': 2,
            'RH': 3,
            'Produção': 4,
        }
        # Retorna o ID para "TI" (ou a entidade raiz) se o setor não for encontrado
        return sector_mapping.get(setor, 0)

    def create_ticket(self, chamado_data: dict) -> int | None:
        """
        Cria um novo ticket no GLPI a partir dos dados do chamado local.

        Args:
            chamado_data (dict): Um dicionário contendo os dados do chamado.
                                 Ex: {'nome': '...', 'setor': '...', ...}

        Returns:
            int | None: O ID do ticket criado no GLPI, ou None em caso de falha.
        """
        if not self.session_token:
            logging.error("Não autenticado. Chame o método authenticate() primeiro.")
            return None

        # Mapeamento dos campos do seu sistema para a estrutura da API do GLPI
        glpi_ticket_data = {
            'name': chamado_data.get('descricao', 'Chamado sem título')[:250],
            'content': f"""
                <p><strong>Solicitante:</strong> {chamado_data.get('nome')}</p>
                <p><strong>Setor:</strong> {chamado_data.get('setor')}</p>
                <p><strong>AnyDesk:</strong> {chamado_data.get('anydesk', 'Não informado')}</p>
                <hr>
                <p><strong>Descrição do Problema:</strong></p>
                <p>{chamado_data.get('descricao')}</p>
                <p><strong>Observações:</strong> {chamado_data.get('observacoes', 'N/A')}</p>
            """,
            'urgency': self._map_priority(chamado_data.get('prioridade', 'Baixa')),
            'entities_id': self._get_entity_id_by_sector(chamado_data.get('setor')),
            '_users_id_requester': 0, # 0 significa que o próprio usuário da API abre o chamado
            'status': 1  # 1 = Novo
        }
        
        try:
            logging.info(f"Criando ticket no GLPI para o solicitante: {chamado_data.get('nome')}")
            response = requests.post(
                f"{self.base_url}/Ticket",
                headers=self.headers,
                json={'input': glpi_ticket_data}
            )
            response.raise_for_status()
            
            ticket_info = response.json()
            logging.info(f"Ticket criado com sucesso! ID no GLPI: {ticket_info['id']}")
            return ticket_info['id']

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao criar ticket no GLPI: {e.response.text if e.response else e}")
            return None

    def close_session(self):
        """
        Encerra a sessão na API do GLPI para liberar o token.
        """
        if self.session_token:
            try:
                logging.info("Encerrando sessão no GLPI.")
                requests.get(f"{self.base_url}/killSession", headers=self.headers)
                self.session_token = None
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro ao encerrar a sessão no GLPI: {e}")
    
    def _map_status(self, status_local: str) -> int:
        """
        Mapeia o status do sistema local para o ID de status do GLPI.
        Estes são IDs comuns, mas podem ser verificados no seu GLPI em Configuração > Itens Intitulados.
        """
        # IDs Padrão do GLPI: 1:Novo, 2:Em atendimento(atribuído), 4:Pendente, 5:Solucionado, 6:Fechado
        mapping = {
            'aberto': 1,
            'iniciado': 2,
            'em andamento': 2,
            'pendente': 4,
            'resolvido': 5,
            'finalizado': 5,
            'concluído': 5,
            'fechado': 6
        }
        # Garante que a comparação não diferencia maiúsculas/minúsculas
        return mapping.get(status_local.lower(), 2) # Retorna 'Em atendimento' como padrão

    def update_ticket_status(self, ticket_id: int, status_local: str) -> bool:
        """
        Atualiza o status de um ticket existente no GLPI.

        Args:
            ticket_id (int): O ID do ticket no GLPI (o nosso glpi_ticket_id).
            status_local (str): O status vindo do seu sistema (ex: "Em andamento").

        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário.
        """
        if not self.session_token:
            logging.error("Não autenticado para atualizar status.")
            return False

        # Mapeia o status local para o ID do GLPI
        status_glpi_id = self._map_status(status_local)
        
        update_data = {'status': status_glpi_id}

        try:
            logging.info(f"Atualizando status do ticket GLPI ID {ticket_id} para {status_glpi_id} ({status_local})")
            response = requests.put(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self.headers,
                json={'input': update_data}
            )
            response.raise_for_status()
            logging.info("Status do ticket no GLPI atualizado com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao atualizar status do ticket no GLPI: {e.response.text if e.response else e}")
            return False

    def add_followup(self, ticket_id: int, content: str) -> bool:
        """
        Adiciona um acompanhamento (observação) a um ticket existente no GLPI.

        Args:
            ticket_id (int): O ID do ticket no GLPI.
            content (str): O texto da observação a ser adicionada.

        Returns:
            bool: True se o acompanhamento foi adicionado, False caso contrário.
        """
        if not self.session_token:
            logging.error("Não autenticado para adicionar acompanhamento.")
            return False

        # O endpoint para acompanhamentos é 'ITILFollowup'
        followup_data = {
            'tickets_id': ticket_id,
            'content': content,
            'is_private': 0  # 0 = Acompanhamento público, 1 = privado
        }
        
        try:
            logging.info(f"Adicionando acompanhamento ao ticket GLPI ID {ticket_id}")
            response = requests.post(
                f"{self.base_url}/ITILFollowup",
                headers=self.headers,
                json={'input': followup_data}
            )
            response.raise_for_status()
            logging.info("Acompanhamento adicionado com sucesso ao GLPI.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao adicionar acompanhamento no GLPI: {e.response.text if e.response else e}")
            return False