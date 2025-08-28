from playwright.sync_api import sync_playwright
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def extrair_sumulas_vinculantes_playwright():
    from playwright.sync_api import sync_playwright, TimeoutError
    from bs4 import BeautifulSoup

    sumulas = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ))
            page = context.new_page()

            try:
                response = page.goto(
                    "https://www.stf.jus.br/portal/jurisprudencia/listarSumulaVinculante.asp",
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                if response.status != 200:
                    print(f"⚠️ Página retornou status {response.status}")
                else:
                    print("✅ Página carregada com sucesso.")

                page.wait_for_selector("table", timeout=15000)
                html = page.content()

                soup = BeautifulSoup(html, "html.parser")
                tabela = soup.find('table')
                if tabela:
                    linhas = tabela.find_all('tr')[1:]
                    for linha in linhas:
                        colunas = linha.find_all('td')
                        if len(colunas) >= 2:
                            numero = colunas[0].get_text(strip=True)
                            texto = colunas[1].get_text(strip=True)
                            sumulas.append((numero, texto, datetime.now()))
                else:
                    print("❌ Ainda não foi possível localizar a tabela.")

            except TimeoutError:
                print("❌ Timeout ao aguardar a tabela.")
            except Exception as e:
                print(f"❌ Erro inesperado durante navegação: {e}")

            browser.close()

    except Exception as e:
        print(f"❌ Erro geral ao iniciar o Playwright: {e}")

    print(f"✅ {len(sumulas)} súmulas extraídas.")
    return sumulas



def criar_banco_dados():
    conn = sqlite3.connect('conteudo_juridico.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sumulas_vinculantes (
            numero TEXT PRIMARY KEY,
            texto TEXT,
            data_atualizacao DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def atualizar_sumulas_bd(sumulas):
    conn = sqlite3.connect('conteudo_juridico.db')
    c = conn.cursor()
    for numero, texto, data in sumulas:
        c.execute('''
            INSERT OR REPLACE INTO sumulas_vinculantes (numero, texto, data_atualizacao)
            VALUES (?, ?, ?)
        ''', (numero, texto, data))
    conn.commit()
    conn.close()

# Execução do processo completo
if __name__ == "__main__":
    criar_banco_dados()
    sumulas = extrair_sumulas_vinculantes_playwright()
    atualizar_sumulas_bd(sumulas)
