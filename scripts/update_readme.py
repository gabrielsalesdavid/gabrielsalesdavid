#!/usr/bin/env python3
# Atualiza seção de repositórios públicos no README.md entre os marcadores
import re
import requests
import subprocess
import sys
from urllib.parse import urlparse

README = 'README.md'
MARKER_START = '<!-- repos-start -->'
MARKER_END = '<!-- repos-end -->'


def get_github_username():
    try:
        out = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], stderr=subprocess.DEVNULL)
        url = out.decode().strip()
        # suportar https e git@ formats
        if url.startswith('git@'):
            # git@github.com:username/repo.git
            path = url.split(':', 1)[1]
            username = path.split('/', 1)[0]
            return username
        else:
            parsed = urlparse(url)
            parts = parsed.path.strip('/').split('/')
            if parts:
                return parts[0]
    except Exception:
        pass
    # fallback: usar nome do repo owner definido
    return 'gabrielsalesdavid'


def fetch_repos(username):
    url = f'https://api.github.com/users/{username}/repos?per_page=200&sort=updated'
    headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'update-readme-script'}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def build_markdown_list(repos):
    lines = []
    for repo in repos:
        name = repo.get('name')
        html_url = repo.get('html_url')
        desc = repo.get('description')
        if desc:
            lines.append(f'- [{name}]({html_url}) — {desc}')
        else:
            lines.append(f'- [{name}]({html_url})')
    return '\n'.join(lines)


def replace_section(readme_path, new_section_md):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = re.compile(re.escape(MARKER_START) + r'.*?' + re.escape(MARKER_END), re.S)
    replacement = MARKER_START + '\n' + new_section_md + '\n' + MARKER_END
    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
    else:
        # markers não encontrados: inserir antes da seção '### 📊 GitHub & Linguagens' se existir
        insert_point = content.find('### 📊 GitHub & Linguagens')
        if insert_point == -1:
            new_content = content + '\n\n' + replacement + '\n'
        else:
            new_content = content[:insert_point] + replacement + '\n\n' + content[insert_point:]
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    username = get_github_username()
    print('Using GitHub user:', username)
    try:
        repos = fetch_repos(username)
    except Exception as e:
        print('Failed to fetch repos:', e)
        sys.exit(1)
    md = build_markdown_list(repos)
    replace_section(README, md)
    print('README updated with', len(repos), 'repos')


if __name__ == '__main__':
    main()
