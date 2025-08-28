import requests

class ApiCamaraClient:
    """
    Um cliente para interagir com a API de Dados Abertos da Câmara dos Deputados.
    """
    def __init__(self, base_url):
        """
        Inicializa o cliente da API.

        :param base_url: A URL base da API da Câmara.
        """
        self.base_url = base_url

    def _fazer_requisicao(self, endpoint, params=None):
        """
        Faz uma requisição GET para um endpoint da API.

        :param endpoint: O endpoint da API a ser chamado (ex: '/proposicoes').
        :param params: Um dicionário de parâmetros de query.
        :return: O JSON da resposta da API ou None em caso de erro.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers={'Accept': 'application/json'})
            response.raise_for_status()  # Lança uma exceção para erros HTTP (4xx ou 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao fazer a requisição para {url}: {e}")
            return None

    def buscar_proposicao(self, sigla_tipo, numero, ano):
        """
        Busca por uma proposição específica.

        :param sigla_tipo: A sigla do tipo da proposição (ex: 'PL').
        :param numero: O número da proposição.
        :param ano: O ano da proposição.
        :return: Um dicionário com os dados da primeira proposição encontrada ou None.
        """
        params = {
            'siglaTipo': sigla_tipo,
            'numero': numero,
            'ano': ano,
            'ordem': 'ASC',
            'ordenarPor': 'id'
        }
        data = self._fazer_requisicao('/proposicoes', params=params)
        if data and data.get('dados'):
            return data['dados'][0]  # Retorna o primeiro item da lista
        return None

    def obter_detalhes_proposicao(self, id_proposicao):
        """
        Obtém os detalhes completos de uma proposição.

        :param id_proposicao: O ID da proposição.
        :return: Um dicionário com os detalhes da proposição ou None.
        """
        data = self._fazer_requisicao(f'/proposicoes/{id_proposicao}')
        return data.get('dados') if data else None

    def obter_autores_proposicao(self, id_proposicao):
        """
        Obtém os autores de uma proposição.

        :param id_proposicao: O ID da proposição.
        :return: Uma lista de dicionários, cada um representando um autor, ou None.
        """
        data = self._fazer_requisicao(f'/proposicoes/{id_proposicao}/autores')
        return data.get('dados') if data else None