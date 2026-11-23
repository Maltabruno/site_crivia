# Relatório — implementação do alinhamento das 21 ofertas no site (R02)

**Data:** 22–23/11/2026 · **Repositório:** `Maltabruno/site_crivia` · **Base:** `a0d7ac5` (main)
**Branch:** `claude/site-adjustments-study-xg2930` · **Commit:** `29062f6` (local; o hash muda ao aplicar com `git am`)

## Estado em uma linha
Implementado e testado localmente. **Não enviado ao GitHub** (push bloqueado com 403: o Claude GitHub App não tem acesso a `Maltabruno/site_crivia`). **Nada publicado.** Preview apresentado só em servidor local.

## Fontes usadas
Plano de correção do site, roteiro editorial e projeção pública do catálogo (revisão R02), todos do pacote de alinhamento, lidos em modo somente leitura.

## O que foi feito em `site_crivia_padrao/`
| Item | Mudança |
|---|---|
| Catálogo | 18 cards em 4 frentes (01–12 preservados; 13–17 e 21 novos). Cada card: dor, o que fazemos, entregas, fora do escopo, CTA; bloco expansível com "se você decide / se você entrega a um cliente", benefícios, referência e disponibilidade. |
| Frente 04 | Bloco `#frente-entrega-cliente` (texto do roteiro) com botão que abre a quarta aba; link no rodapé. |
| Entradas 18/19/20 | Âncoras `produto-1/2/3` preservadas; rótulos "OFERTA 18/19/20"; entregas, limites e assunto do contato vêm dos mesmos dados. |
| Dados | `catalogo-publico.json` (projeção pública R02). Bloco `CATALOGO` do `app.js` gerado por `scripts/gerar_catalogo.py` (`python -I scripts/gerar_catalogo.py`). |
| Navegação | `#servico-NN` abre a frente certa e rola até o card; abas com setas/Home/End, `aria-controls`, tabpanel. |
| CTA | Assunto "NN — Nome" via `data-assunto`; WhatsApp `5527996971800` e e-mail inalterados; sem formulário nem backend. |
| Imagens | 12 existentes preservadas; novos cards usam cabeçalho em CSS (sem imagem inventada). |
| Texto | "Doze produtos" → "Dezoito produtos em quatro frentes"; cache-bust `?v=20261122a`. |

Arquivos do commit (7): `README.md`, `scripts/gerar_catalogo.py` (novo), `site_crivia_padrao/{app.js,index.html,styles.css,catalogo-publico.json (novo)}`, `tests/test_site_padrao.py`.

## Verificação executada
- `python -I -m unittest discover -s tests -v`: **57 testes OK** (44 antes da mudança). Novos testes semânticos: 21 números, 18 cards + 3 entradas, 4 grupos sem órfão/duplicado, IDs e âncoras legadas, JSON sem chaves privadas/"R$"/"%", equivalência JSON × `app.js`, gerador idempotente, CTA com código+nome, sem `fetch`/formulário.
- `node --check site_crivia_padrao/app.js`: OK.
- Playwright (1366, 768, 390, 360 px): sem rolagem horizontal, sem erro de console, sem imagem quebrada; 4 abas com os cards certos; teclado nas abas; CTA do card 13 e da entrada 19 com assunto correto; botão da frente 04 abre a aba 4; `#servico-16` abre a aba 4 e rola ao card; screenshots conferidos.
- Patch aplicado em clone limpo de `a0d7ac5`: aplica sem conflito e os testes do site passam.

## Como aplicar no desktop (Git Bash, na pasta do repositório)
```
git stash push -m "imagens" -- site_crivia_padrao/assets/experiencias/integracao.jpg site_crivia_padrao/assets/experiencias/planejamento.jpg   # só se aparecerem no git status
git checkout -b claude/site-adjustments-study-xg2930
git am ../catalogo-r02.patch
python -I -m unittest discover -s tests -v
git push -u origin claude/site-adjustments-study-xg2930
git stash pop   # se usou o stash
```
SHA-256 do patch: `0e3569dddbc044b4cbbfede13dfaf6cbea089f04aff1cbe5fbf844eebdf34198`. Sem `git add -A`, sem PR e sem merge no `main` sem OK de Bruno (README: nada vai para a hospedagem sem o OK dele).

## Pendências e riscos (não resolvidos)
1. **Disponibilidade 13–17 e 21:** o plano exige confirmação de responsável, procedimento e capacidade antes de publicar, ou marcar "em estruturação". Hoje todos mostram só "Consulte o escopo e a disponibilidade para o seu caso." dentro do bloco expansível.
2. **Fonte pública com ID interno:** um campo da oferta 18 em `catalogo-publico.json` cita um identificador interno da oferta 21. Não é exibido, mas o arquivo é público; corrigir na fonte.
3. **Textos antigos das entradas** (não reescritos, fora do escopo): o parágrafo da oferta 20 fala em "recomendação técnica de liberação ou retenção" de medição, que pode destoar do limite do cadastro ("não presume decisão de pagamento"). Revisar. Os painéis seguem como "exemplo ilustrativo".
4. **Não feito:** atualização das bases documentais internas, promoção dos documentos e comparador do Painel (fora deste repositório), preview publicado para revisão de Bruno, publicação.
5. **Desvio do plano:** branch usada foi a designada pela sessão, não `codex/alinhamento-portfolio-21`. As duas imagens locais citadas no plano não estavam modificadas neste clone.

## Registro (conforme o plano)
- Implementação aceita em preview: **não** (só conferência local).
- Commit identificado: `29062f6` local, **não enviado**.
- Publicação conferida por URL: **não**.
