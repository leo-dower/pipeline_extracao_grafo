import requests
import json

class QueridoDiarioClient:
    """
    Um cliente para interagir com a API do Querido Diário.
    """
    def __init__(self, base_url, api_key):
        """
        Inicializa o cliente da API do Querido Diário.

        :param base_url: A URL base da API do Querido Diário.
        :param api_key: A chave da API para autenticação.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {'Authorization': f'Token {self.api_key}', 'Accept': 'application/json'}

    def _fazer_requisicao(self, endpoint, params=None):
        """
        Faz uma requisição GET para um endpoint da API do Querido Diário.

        :param endpoint: O endpoint da API a ser chamado (ex: '/api/search').
        :param params: Um dicionário de parâmetros de query.
        :return: O JSON da resposta da API ou None em caso de erro.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()  # Lança uma exceção para erros HTTP (4xx ou 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao fazer a requisição para {url}: {e}")
            return None

    def buscar_diarios_por_municipio_e_data(self, municipality_id, start_date, end_date=None):
        """
        Busca diários por ID do município e período.

        :param municipality_id: O ID do município.
        :param start_date: Data de início no formato YYYY-MM-DD.
        :param end_date: Data de fim no formato YYYY-MM-DD (opcional).
        :return: Uma lista de dicionários, cada um representando um diário.
        """
        all_results = []
        page = 1
        while True:
            params = {
                'municipality_id': municipality_id,
                'published_since': start_date,
                'page': page,
                'size': 100  # Máximo permitido pela API
            }
            if end_date:
                params['published_until'] = end_date

            data = self._fazer_requisicao('/gazettes', params=params)
            if data and data.get('results'):
                all_results.extend(data['results'])
                if len(data['results']) < data['size']:
                    break
                page += 1
            else:
                break
        return all_results

    def buscar_diarios_por_termo(self, query, municipality_id=None, start_date=None, end_date=None):
        """
        Busca diários por termo de busca.

        :param query: Termo(s) de busca.
        :param municipality_id: ID do município (opcional).
        :param start_date: Data de início no formato YYYY-MM-DD (opcional).
        :param end_date: Data de fim no formato YYYY-MM-DD (opcional).
        :return: Uma lista de dicionários, cada um representando um diário.
        """
        all_results = []
        page = 1
        while True:
            params = {
                'query': query,
                'page': page,
                'size': 100  # Máximo permitido pela API
            }
            if municipality_id:
                params['municipality_id'] = municipality_id
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date

            data = self._fazer_requisicao('/search', params=params)
            if data and data.get('results'):
                all_results.extend(data['results'])
                if len(data['results']) < data['size']:
                    break
                page += 1
            else:
                break
        return all_results

    def obter_conteudo_diario(self, file_url):
        """
        Obtém o conteúdo de um diário a partir de sua URL (geralmente PDF).

        :param file_url: URL para o arquivo PDF do diário.
        :return: O conteúdo binário do arquivo ou None em caso de erro.
        """
        try:
            response = requests.get(file_url, headers=self.headers)
            response.raise_for_status()
            return response.content  # Retorna o conteúdo binário
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter conteúdo do diário em {file_url}: {e}")
            return None