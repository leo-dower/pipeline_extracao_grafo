import requests
import json

url = "https://jurisprudencia.stf.jus.br/pages/search"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Este é o corpo básico (payload) da pesquisa de súmulas vinculantes
payload = {
    "classeNumeroIncidente": "vinculante",
    "base": "sumulas",
    "is_vinculante": "true",
    "pagina": 1,
    "tamanhoPagina": 10  # você pode aumentar esse valor para obter mais resultados por página
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Resultados encontrados: {len(data.get('resultados', []))}\n")
    for item in data.get('resultados', []):
        print(f"Número: {item.get('numero')}")
        print(f"Ementa: {item.get('ementa')}")
        print(f"Link: {item.get('linkVisualizacao')}")
        print("-" * 40)
else:
    print(f"❌ Erro na requisição: {response.status_code}")
