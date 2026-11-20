# Como publicar no GitHub

[Voltar ao projeto](../README.md)

Primeiro, crie um repositório **vazio** no GitHub, sem README, licença nem
`.gitignore`: esses arquivos já vêm no projeto.

## Usando Git (recomendado)

Na pasta do projeto, confira o que será enviado:

```bash
git status --short
```

A lista deve ter apenas o código, a documentação, o firmware, o áudio em
`assets/audio/` e o `Iniciar R2D2.bat`. Pastas como `.venv/`, `data/`, `outputs/`,
`controle/`, `dist/` e `backup_antes_rastreamento/` não devem aparecer.

Esta cópia local já foi inicializada com a branch `main`. Se estiver usando uma
cópia extraída do ZIP, execute primeiro `git init -b main`. Depois:

```bash
git add .
git diff --cached --stat
git commit -m "R2D2: assistente de voz com Arduino"
git remote add origin https://github.com/SEU_USUARIO/R2D2.git
git push -u origin main
```

Substitua `SEU_USUARIO/R2D2` pelo proprietário e pelo nome do repositório criado.
O envio exige autenticação na sua conta do GitHub. Se o Git pedir identificação
para o commit, configure `git config user.name "Seu nome"` e
`git config user.email "Seu email"` nesta pasta.

## Usando o navegador

O pacote `dist/R2D2-github.zip` tem exatamente os arquivos que devem ir para o
repositório.

1. Extraia o ZIP em uma pasta separada.
2. Abra o repositório no GitHub e use **Add file → Upload files**.
3. Arraste o **conteúdo da pasta `R2D2` extraída**, mantendo as subpastas.
4. Confira se `.gitignore` e `.gitattributes` foram incluídos. Arquivos que começam
   com ponto ficam ocultos no Windows; ative **Exibir → Itens ocultos** no Explorador.
5. Confirme o commit.

Envie os arquivos extraídos, não o ZIP como único arquivo do repositório. O
`.gitignore` só vale para o Git local: ele não filtra arquivos escolhidos
manualmente no navegador.

O pacote é uma cópia desta versão. Se editar o projeto depois, use Git para enviar
a versão atual ou gere um novo pacote.

## Arquivos que ficam só na sua máquina

| Caminho | Conteúdo |
|---|---|
| `.venv/` | Dependências instaladas localmente |
| `data/` | Agenda pessoal (`agenda.txt`) |
| `outputs/` | Capturas de tela e gravações de diagnóstico |
| `controle/` | Sinal de parada usado pelo `Iniciar R2D2.bat` |
| `backup_antes_rastreamento/` | Cópia dos arquivos anteriores ao rastreamento |
| `dist/` | ZIP preparado para distribuição |
| `.env` e `.env.*` | Possíveis configurações privadas |
| `__pycache__/` | Cache do Python |

Configure chaves de API por variáveis de ambiente, conforme o
[manual](manual.md#configurações-opcionais). O projeto não carrega `.env`
automaticamente.
