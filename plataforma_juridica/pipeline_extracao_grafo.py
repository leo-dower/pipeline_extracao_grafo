import spacy
from spacy.matcher import Matcher
from neo4j import GraphDatabase
import os
import re
import json
from pypdf import PdfReader
import configparser
from api_camara_client import ApiCamaraClient

# --- FUNÇÕES DE CONFIGURAÇÃO ---
def ler_configuracoes(config_file='plataforma_juridica/config.ini'):
    """Lê as configurações do arquivo config.ini."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Arquivo de configuração '{config_file}' não encontrado.")
    config.read(config_file)
    return config

# --- CLASSE PARA INTERAGIR COM O NEO4J ---
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def execute_query(self, query, parameters=None):
        with self._driver.session() as session:
            return session.execute_write(self._execute_transaction, query, parameters)

    @staticmethod
    def _execute_transaction(tx, query, parameters):
        result = tx.run(query, parameters)
        return [record for record in result]

    def create_relationship(self, source_label, source_props, target_label, target_props, rel_type):
        source_match = ", ".join([f'{k}: $source_{k}' for k in source_props])
        target_match = ", ".join([f'{k}: $target_{k}' for k in target_props])
        
        query = f"""
        MATCH (a:{source_label} {{ {source_match} }})
        MATCH (b:{target_label} {{ {target_match} }})
        MERGE (a)-[r:{rel_type}]->(b)
        RETURN type(r)
        """
        params = {f'source_{k}': v for k, v in source_props.items()}
        params.update({f'target_{k}': v for k, v in target_props.items()})
        
        self.execute_query(query, params)
        print(f"Relação [:{rel_type}] criada entre {source_props} e {target_props}")

# --- FUNÇÕES DO PIPELINE ---

def carregar_modelo_spacy():
    """Carrega o modelo de linguagem em português do spaCy."""
    try:
        nlp = spacy.load("pt_core_news_sm")
        print("Modelo spaCy 'pt_core_news_sm' carregado com sucesso.")
        return nlp
    except OSError:
        print("Modelo 'pt_core_news_sm' não encontrado.")
        return None

def ler_texto_de_pdf(pdf_path):
    """Lê o texto de um arquivo PDF usando pypdf."""
    print(f"Lendo texto do PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Erro: Arquivo PDF não encontrado em '{pdf_path}'.")
        return None

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        print(f"Texto extraído do PDF (total de {len(text)} caracteres).")
        return text
    except Exception as e:
        print(f"Erro ao extrair texto do PDF '{pdf_path}': {e}")
        return None

def ler_textos_de_diretorio_pdfs(pdf_directory_path):
    """Lê todos os arquivos PDF de um diretório e retorna seus textos."""
    print(f"Procurando PDFs no diretório: {pdf_directory_path}")
    if not os.path.isdir(pdf_directory_path):
        print(f"Erro: Diretório '{pdf_directory_path}' não encontrado.")
        return []

    pdf_texts = []
    for filename in os.listdir(pdf_directory_path):
        if filename.lower().endswith(".pdf"):
            full_path = os.path.join(pdf_directory_path, filename)
            text = ler_texto_de_pdf(full_path)
            if text:
                pdf_texts.append((filename, text))
    print(f"Total de {len(pdf_texts)} PDFs processados do diretório.")
    return pdf_texts

def normalizar_entidade(rule_id, entity_text):
    """Normaliza o texto da entidade para um formato padrão."""
    text = entity_text.strip().lower()
    
    try:
        if rule_id == 'ARTIGO':
            num = re.search(r'\d+', text).group()
            return f"Art. {num}"
        
        elif rule_id == 'LEI':
            # A normalização da LEI agora é apenas para limpar o texto
            return entity_text.strip()
        
        elif rule_id == 'SUMULA':
            num_match = re.search(r'\d+', text)
            if num_match:
                num = num_match.group(0)
                if 'vinculante' in text or 'sv' in text:
                    return f"Súmula Vinculante {num}"
                return f"Súmula {num}"

        elif rule_id == 'CONSTITUICAO':
            return "Constituição Federal de 1988"

        elif rule_id == 'CODIGO':
            if 'processo civil' in text: return "Código de Processo Civil"
            if 'processo penal' in text: return "Código de Processo Penal"
            if 'civil' in text: return "Código Civil"
            if 'penal' in text: return "Código Penal"
            if 'tributário' in text: return "Código Tributário Nacional"
            if 'defesa do consumidor' in text: return "Código de Defesa do Consumidor"
            return entity_text.title()

    except (AttributeError, IndexError):
        print(f"  [Aviso] Não foi possível normalizar '{entity_text}' para a regra {rule_id}. Usando texto original.")
        return entity_text.strip()

    return entity_text.strip()

def extrair_e_popular_grafo(nlp, neo4j_conn, camara_client, mapa_leis, document_name, document_text):
    """Função principal para extrair entidades dos textos e popular o grafo Neo4j."""
    print(f"\nIniciando extração e povoamento para o documento: {document_name}")
    
    matcher = Matcher(nlp.vocab)

    pattern_lei = [{"LOWER": {"IN": ["lei", "decreto-lei"]}}, {"LOWER": "nº"}, {"TEXT": {"REGEX": "^\\d{1,3}(\\.\\d{3})*\\/\\d{4}$"}}]
    matcher.add("LEI", [pattern_lei])

    pattern_artigo = [{"LOWER": {"IN": ["artigo", "art.", "art"]}}, {"IS_DIGIT": True}]
    matcher.add("ARTIGO", [pattern_artigo])

    pattern_sumula = [{"LOWER": {"IN": ["súmula", "sv"]}}, {"LOWER": "vinculante", "OP": "?"}, {"LOWER": {"IN": ["nº", "n."]}, "OP": "?"}, {"IS_DIGIT": True}]
    matcher.add("SUMULA", [pattern_sumula])

    pattern_cf_completa = [{"LOWER": "constituição"}, {"LOWER": "da"}, {"LOWER": "república"}, {"LOWER": "federativa"}, {"LOWER": "do"}, {"LOWER": "brasil"}]
    pattern_cf_federal = [{"LOWER": "constituição"}, {"LOWER": "federal"}]
    pattern_cf_88 = [{"LOWER": "constituição"}, {"LOWER": "de"}, {"LOWER": "1988"}]
    pattern_cf_sigla = [{"TEXT": {"IN": ["CF", "CRFB", "CF/88"]}}]
    matcher.add("CONSTITUICAO", [pattern_cf_completa, pattern_cf_federal, pattern_cf_88, pattern_cf_sigla])

    pattern_codigo_simples = [{"LOWER": "código"}, {"LOWER": {"IN": ["civil", "penal", "tributário", "eleitoral", "florestal"]}}]
    pattern_codigo_processo = [{"LOWER": "código"}, {"LOWER": "de"}, {"LOWER": "processo"}, {"LOWER": {"IN": ["civil", "penal"]}}]
    pattern_codigo_consumidor = [{"LOWER": "código"}, {"LOWER": "de"}, {"LOWER": "defesa"}, {"LOWER": "do"}, {"LOWER": "consumidor"}]
    matcher.add("CODIGO", [pattern_codigo_simples, pattern_codigo_processo, pattern_codigo_consumidor])

    neo4j_conn.execute_query("MERGE (d:Documento {nome: $nome})", {"nome": document_name})
    
    doc = nlp(document_text)
    matches = matcher(doc)

    if not matches:
        print("  Nenhuma citação encontrada neste documento com os padrões atuais.")
        return

    for match_id, start, end in matches:
        span = doc[start:end]
        rule_id = nlp.vocab.strings[match_id]
        entity_text = re.sub(r'[.,\s]*$', '', span.text.strip())
        
        normalized_text = normalizar_entidade(rule_id, entity_text)
        if not normalized_text:
            continue

        print(f"  - Encontrado: '{entity_text}' ({rule_id}) -> Normalizado para: '{normalized_text}'")
        
        entity_label = rule_id.capitalize()
        
        props = {"id": normalized_text}
        neo4j_conn.execute_query(f"MERGE (e:{entity_label} {{id: $id}})", props)
        
        neo4j_conn.create_relationship(
            "Documento", {"nome": document_name},
            entity_label, {"id": normalized_text},
            "CITA"
        )

        if rule_id == 'LEI':
            projeto_origem = mapa_leis.get(normalized_text)
            if projeto_origem:
                sigla = projeto_origem['sigla']
                numero = projeto_origem['numero']
                ano = projeto_origem['ano']

                print(f"  Buscando proposição na API da Câmara: {sigla} {numero}/{ano}")
                proposicao = camara_client.buscar_proposicao(sigla, numero, ano)
                
                if proposicao and proposicao.get('id'):
                    prop_id = proposicao['id']
                    detalhes = camara_client.obter_detalhes_proposicao(prop_id)
                    
                    if detalhes:
                        query = f"""
                        MATCH (l:Lei {{id: $id}})
                        SET l.ementa = $ementa, l.status = $status, l.urlInteiroTeor = $url
                        """
                        params = {
                            'id': normalized_text,
                            'ementa': detalhes.get('ementa'),
                            'status': detalhes.get('statusProposicao', {}).get('descricaoSituacao'),
                            'url': detalhes.get('urlInteiroTeor')
                        }
                        neo4j_conn.execute_query(query, params)
                        print(f"    -> Nó :Lei enriquecido com ementa e status.")

                    autores = camara_client.obter_autores_proposicao(prop_id)
                    if autores:
                        for autor in autores:
                            props_autor = {'nome': autor['nome'], 'tipo': autor.get('tipo', 'Indefinido')}
                            neo4j_conn.execute_query("MERGE (a:Autor {nome: $nome}) SET a += $props", {'nome': autor['nome'], 'props': props_autor})
                            neo4j_conn.create_relationship(
                                "Autor", {'nome': autor['nome']},
                                "Lei", {'id': normalized_text},
                                "AUTOR_DE"
                            )
                            print(f"    -> Relação [:AUTOR_DE] criada para o autor: {autor['nome']}")
            else:
                print(f"  [Aviso] Lei '{normalized_text}' não encontrada no arquivo de mapeamento.")

# --- FUNÇÃO PRINCIPAL DE EXECUÇÃO ---
def main():
    print("--- Iniciando Pipeline de Extração para o Grafo de Conhecimento Jurídico ---")
    
    try:
        config = ler_configuracoes()
        neo4j_uri = config['NEO4J']['URI']
        neo4j_user = config['NEO4J']['USER']
        neo4j_password = config['NEO4J']['PASSWORD']
        pdf_directory_to_process = config['PATHS']['PDF_DIRECTORY']
        camara_api_url = config['API_CAMARA']['BASE_URL']
        
        neo4j_conn = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)
        print("Conexão com Neo4j estabelecida.")
        
        camara_client = ApiCamaraClient(camara_api_url)
        print("Cliente da API da Câmara inicializado.")

        with open('plataforma_juridica/mapeamento_leis.json', 'r', encoding='utf-8') as f:
            mapeamento_leis = json.load(f)
        mapa_leis = {item['lei']: item['projeto_origem'] for item in mapeamento_leis}
        print("Mapeamento de leis carregado.")

    except (FileNotFoundError, KeyError) as e:
        print(f"[ERRO] Erro ao ler o arquivo de configuração ou mapeamento: {e}")
        return
    except Exception as e:
        print(f"[ERRO] Falha inesperada: {e}")
        return

    nlp = carregar_modelo_spacy()
    if nlp is None: return

    processed_pdfs = ler_textos_de_diretorio_pdfs(pdf_directory_to_process)
    if not processed_pdfs:
        print(f"Nenhum PDF encontrado ou processado no diretório '{pdf_directory_to_process}'. Encerrando.")
        return

    for filename, text in processed_pdfs:
        extrair_e_popular_grafo(nlp, neo4j_conn, camara_client, mapa_leis, filename, text)

    neo4j_conn.close()
    print("\n--- Pipeline concluído ---")


if __name__ == "__main__":
    main()