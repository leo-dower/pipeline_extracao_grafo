import re
import json

def gerar_mapeamento(arquivo_entrada, arquivo_saida):
    """
    Lê um arquivo de texto com dados de leis, processa o conteúdo
    e gera um arquivo JSON estruturado com o mapeamento.
    """
    print(f"Lendo dados de '{arquivo_entrada}'...")
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except FileNotFoundError:
        print(f"[ERRO] Arquivo de entrada '{arquivo_entrada}' não encontrado.")
        return

    mapeamento = []
    
    # Divide o arquivo em blocos de registro usando '---' como separador
    registros = conteudo.strip().split('---')
    
    print(f"Processando {len(registros)} registro(s)...")

    for registro in registros:
        if not registro.strip():
            continue

        # Expressões regulares para extrair os dados
        lei_match = re.search(r'Lei: (Lei nº [\d\.]+\/\d{4})', registro)
        origem_match = re.search(r'Origem: .* \((.+)\) nº ([\d\.]+)\/(\d{4})', registro)

        if lei_match and origem_match:
            lei_str = lei_match.group(1)
            sigla = origem_match.group(1)
            numero = origem_match.group(2).replace('.', '')
            ano = origem_match.group(3)

            mapeamento.append({
                "lei": lei_str,
                "projeto_origem": {
                    "sigla": sigla,
                    "numero": numero,
                    "ano": ano
                }
            })
            print(f"  - Mapeamento encontrado: {lei_str} -> {sigla} {numero}/{ano}")
        else:
            print(f"  [Aviso] Registro não pôde ser processado:\n{registro.strip()}\n")

    print(f"Salvando mapeamento estruturado em '{arquivo_saida}'...")
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, indent=4, ensure_ascii=False)
        
    print("Mapeamento gerado com sucesso!")

if __name__ == '__main__':
    input_file = 'plataforma_juridica/repositorio_leis.txt'
    output_file = 'plataforma_juridica/mapeamento_leis.json'
    gerar_mapeamento(input_file, output_file)
