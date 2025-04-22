# SQLi Dork Scanner

![script](https://github.com/user-attachments/assets/1009dc8b-b353-4224-8675-63724aaa605f)

Ferramenta de busca e detecção automatizada de possíveis vulnerabilidades de **SQL Injection** a partir de **dorks** (Google Hacking), utilizando **múltiplos motores de busca** com **paralelismo extremo e assíncrono** via `trio` + `httpx`.

---

## Wordlist:

- Ele tem uma wordlist pequena apenas para servir como guia de utilização. Você poderá alterar o conteúdo dessa wordlist adicionando suas próprias dorks!<br><br>
- Quanto mais dorks adicionadas **melhor será o resultado** caso a dork seja boa!

## Funcionalidades

- **Coleta URLs** automaticamente usando dorks em 9 motores de busca diferentes:
  - Google
  - Bing
  - Yahoo
  - Qwant
  - StartPage
  - Dogpile
  - Mojeek
  - Brave Search
  - Yandex

- **Filtra URLs com parâmetros** (`?id=1`) para teste.
- **Injeta payloads** de SQL Injection simulando ataques básicos.
- **Confirma vulnerabilidades** analisando o conteúdo das respostas.
- **Salva os resultados confirmados** em um arquivo `Resultado.json`.

---

## Por que tão rápido?

- **Paralelismo real com Trio**: execução de centenas de tarefas assíncronas com leveza.
- **HTTPX assíncrono**: conexões persistentes e altamente otimizadas para redes.
- **Altamente escalável**: suporte para wordlists extensas com milhares de dorks.
- **Sem travamentos ou lentidão**, mesmo em execuções prolongadas.

---

## Como usar:

### Modo automático com wordlist (crie uma wordlist com inúmeras Dorks e deixe o script trabalhar)
    pip install -r requirements.txt
    python3 scanner.py --alt

### Modo manual (1 dork por vez):
    pip install -r requirements.txt
    python3 scanner.py
