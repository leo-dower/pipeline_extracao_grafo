from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

# --- NOVA FUNÇÃO DE EXTRAÇÃO COM SELENIUM ---
def extrair_sumulas_vinculantes():
    url = "https://jurisprudencia.stf.jus.br/pages/search?classe=SV"
    print(f"Acessando URL com Selenium: {url}")

    # Configura o serviço do Chrome para baixar o driver automaticamente
    service = ChromeService(ChromeDriverManager().install())
    
    # Configura as opções do Chrome para rodar em modo "headless" (sem abrir janela)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=service, options=options)
    sumulas = []

    try:
        driver.get(url)
        # Espera até 20 segundos para que o container com os resultados apareça
        # A classe 'result-container' é um palpite inicial, pode precisar de ajuste.
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.result-container"))
        )
        print("Página carregada e container de resultados encontrado.")

        # Pega o HTML final depois do carregamento do JavaScript
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Tenta encontrar os cards de resultado
        cards = soup.find_all("div", class_="result-card")
        print(f"{len(cards)} cards de resultado encontrados.")

        for card in cards:
            numero_tag = card.find("h6")
            texto_tag = card.find("p", class_="result-card-text")
            if numero_tag and texto_tag:
                # Extrai o número da Súmula do texto 'Súmula Vinculante X'
                numero = numero_tag.get_text(strip=True).split(" ")[-1]
                texto = texto_tag.get_text(strip=True)
                sumulas.append((numero, texto, datetime.now()))

    except Exception as e:
        print(f"Ocorreu um erro durante a extração com Selenium: {e}")
    finally:
        driver.quit()
        print("Navegador Selenium fechado.")

    return sumulas

# --- FUNÇÕES DE BANCO DE DADOS (sem alteração) ---
def criar_banco_dados():
    conn = sqlite3.connect('conteudo_juridico.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sumulas_vinculantes (numero TEXT PRIMARY KEY, texto TEXT, data_atualizacao DATETIME)''')
    conn.commit()
    conn.close()

def atualizar_sumulas_bd(sumulas):
    if not sumulas: 
        print("Nenhuma súmula encontrada para atualizar no banco de dados.")
        return
    conn = sqlite3.connect('conteudo_juridico.db')
    c = conn.cursor()
    for numero, texto, data in sumulas:
        c.execute('''INSERT OR REPLACE INTO sumulas_vinculantes (numero, texto, data_atualizacao) VALUES (?, ?, ?)''', (numero, texto, data))
    conn.commit()
    conn.close()
    print(f"{len(sumulas)} súmulas salvas/atualizadas no banco de dados.")

# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    print("Iniciando processo de extração de Súmulas Vinculantes...")
    criar_banco_dados()
    sumulas_extraidas = extrair_sumulas_vinculantes()
    atualizar_sumulas_bd(sumulas_extraidas)
    print("Processo concluído.")
