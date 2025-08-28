from playwright.sync_api import sync_playwright

def capturar_requisicao_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()  # ← Certifique-se de que esta linha está aqui!

        def interceptar(route, request):
            if "pages/search" in request.url and request.method == "POST":
                print("=== Requisição Interceptada ===")
                print("URL:", request.url)
                print("Método:", request.method)
                print("Headers:", request.headers)
                print("Post data:", request.post_data)
                route.continue_()
            else:
                route.continue_()

        context.route("**/*", interceptar)

        # Agora sim: abrir a página e esperar CAPTCHA
        page.goto("https://jurisprudencia.stf.jus.br/pages/search?classeNumeroIncidente=vinculante&base=sumulas&is_vinculante=true")

        print("➡️ Resolva o CAPTCHA manualmente na janela aberta.")
        input("⏳ Pressione [ENTER] aqui no terminal depois de resolver o CAPTCHA para continuar...")

        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    capturar_requisicao_search()
