
import subprocess
import ctypes
import sys
import logging
import os
from pathlib import Path

# --- Configuração do Logging ---
LOG_FILE = Path(__file__).parent / "uninstall_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# --- Listas de Programas a Desinstalar ---

# Nomes parciais ou curingas para aplicativos da Microsoft Store (UWP)
# O script buscará por pacotes que contenham estes nomes.
UWP_APPS_TO_UNINSTALL = [
    "*GamingApp*",                      # Assistência para Jogos (pode variar)
    "*Windows11InstallationAssistant*", # Assistente de Instalação do Windows 11
    "*BingWeather*",                    # Clima
    "*Journal*",                        # Diário (se for o Microsoft Journal)
    "*MicrosoftFamilySafety*",          # Family
    "*FeedbackHub*",                    # Hub de Comentários
    "*Clipchamp*",                      # Microsoft Clipchamp
    "*MicrosoftToDo*",                  # Microsoft To Do
    "*Whiteboard*",                     # Microsoft Whiteboard
    "*StickyNotes*",                    # Notas Autoadesivas
    "*BingNews*",                       # Notícias
    "*OutlookForWindows*",              # Outlook (novo)
    "*SolitaireCollection*",            # Solitaire & Casual Games
    "*Xbox*",                           # Todos os componentes principais do Xbox
    # Adicionados com base em nomes comuns de "bloatware"
    "*YourPhone*",                      # Seu Telefone
    "*ZuneVideo*",                      # Filmes e TV
    "*ZuneMusic*",                      # Groove Music
    "*OneNote*",                        # OneNote (versão UWP)
    "*SkypeApp*",                       # Skype
    "*GetHelp*",                        # Obter Ajuda
    "*OfficeHub*",                      # App do Office
    "*People*",                         # Pessoas
    "*Wallet*",                         # Carteira
    "*PowerAutomate*",                  # Power Automate
    "*MixedReality.Portal*",            # Portal de Realidade Mista
]

# Nomes exatos para programas tradicionais (Win32) que aparecem no WMIC
# Adicione aqui nomes exatos se souber de algum programa Win32 para remover.
WIN32_APPS_TO_UNINSTALL = [
    "Microsoft Web Deploy", # Exemplo, conforme sua lista
    "Live Wallpapers",      # Suposição para "livewallpapers servisse"
]

# --- Funções de Desinstalação ---

def run_powershell_command(command):
    """Executa um comando PowerShell e faz o log do resultado."""
    full_command = f"powershell.exe -ExecutionPolicy Bypass -Command "{command}""
    logging.info(f"Executando PowerShell: {command}")
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.stdout:
            logging.info(f"Saída: {result.stdout.strip()}")
        if result.stderr:
            logging.error(f"Erro: {result.stderr.strip()}")
        return result.stdout.strip()
    except Exception as e:
        logging.critical(f"Falha crítica ao executar comando PowerShell: {e}")
        return None

def uninstall_uwp_apps():
    """Desinstala aplicativos UWP com base na lista UWP_APPS_TO_UNINSTALL."""
    logging.info("--- Iniciando desinstalação de Aplicativos da Store (UWP) ---")
    for app_pattern in UWP_APPS_TO_UNINSTALL:
        logging.info(f"Procurando por pacotes correspondentes a: '{app_pattern}'")
        # Comando para encontrar os pacotes
        find_command = f"Get-AppxPackage -AllUsers '{app_pattern}' | Select-Object -ExpandProperty PackageFullName"
        package_full_names = run_powershell_command(find_command)

        if not package_full_names:
            logging.info(f"Nenhum pacote encontrado para '{app_pattern}'.")
            continue

        # Itera sobre cada pacote encontrado (pode haver mais de um)
        for package_name in package_full_names.splitlines():
            if package_name:
                logging.info(f"Encontrado: '{package_name}'. Tentando remover...")
                # Cuidado especial com pacotes de experiência de idioma
                if "LanguageExperiencePack" in package_name:
                    logging.warning(f"IGNORANDO a remoção do Pacote de Experiência de Idioma para segurança: {package_name}")
                    continue
                
                # Comando para remover o pacote
                remove_command = f"Remove-AppxPackage -Package '{package_name}' -AllUsers"
                run_powershell_command(remove_command)
                
                # Comando de provisionamento para evitar reinstalação
                remove_provisioned_command = f"Get-AppxProvisionedPackage -Online | Where-Object {{ $_.PackageName -like '*{package_name.split('_')[1]}*' }} | Remove-AppxProvisionedPackage -Online"
                run_powershell_command(remove_provisioned_command)

def uninstall_win32_apps():
    """Desinstala programas Win32 com base na lista WIN32_APPS_TO_UNINSTALL."""
    logging.info("--- Iniciando desinstalação de Programas Tradicionais (Win32) ---")
    for app_name in WIN32_APPS_TO_UNINSTALL:
        logging.info(f"Procurando por programa: '{app_name}'")
        # Comando WMIC para desinstalar
        command = f'wmic product where name="{app_name}" call uninstall /nointeractive'
        logging.info(f"Executando WMIC: {command}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if "ReturnValue = 0" in result.stdout:
                logging.info(f"Sucesso ao desinstalar '{app_name}'.")
            elif "No Instance(s) Available" in result.stdout:
                logging.warning(f"Programa '{app_name}' não encontrado via WMIC.")
            else:
                logging.error(f"Falha ou resultado inesperado ao desinstalar '{app_name}'. Saída: {result.stdout.strip()} | Erro: {result.stderr.strip()}")
        except Exception as e:
            logging.critical(f"Falha crítica ao executar WMIC para '{app_name}': {e}")

# --- Função Principal ---

def main():
    """Função principal que verifica permissões e executa as desinstalações."""
    # Verifica se o script está sendo executado como administrador
    try:
        is_admin = (os.getuid() == 0)
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        logging.error("ERRO: Este script precisa ser executado com privilégios de Administrador.")
        logging.error("Por favor, clique com o botão direito no arquivo .py e selecione 'Executar como administrador'.")
        # Pausa para o usuário poder ler a mensagem antes de fechar
        input("Pressione Enter para sair...")
        sys.exit(1)

    logging.info("Executando com privilégios de Administrador.")
    
    # Descomente as seções que deseja executar
    uninstall_uwp_apps()
    uninstall_win32_apps()
    
    logging.info("--- Processo de desinstalação concluído ---")
    logging.info(f"Um log detalhado foi salvo em: {LOG_FILE}")
    input("Pressione Enter para finalizar...")

if __name__ == "__main__":
    # Adicionado 'os' ao escopo local da função main para a verificação de admin
    import os
    main()
