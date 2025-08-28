import requests

# Montando a URL com parâmetros diretamente na querystring (GET)
url = (
    "https://jurisprudencia.stf.jus.br/pages/search"
    "?classeNumeroIncidente=vinculante"
    "&base=sumulas"
    "&is_vinculante=true"
    "&pagina=1"
    "&tamanhoPagina=10"
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    resultados = data.get("resultados", [])
    print(f"✅ Resultados encontrados: {len(resultados)}\n")
    for item in resultados:
        print(f"Número: {item.get('numero')}")
        print(f"Ementa: {item.get('ementa')}")
        print(f"Link: {item.get('linkVisualizacao')}")
        print("-" * 40)
else:
    print(f"❌ Erro na requisição: {response.status_code}")
