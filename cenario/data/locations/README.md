# Localidades do formulário

- Fonte: API de Localidades do IBGE (https://servicodados.ibge.gov.br/api/v1/localidades) e API de Países do IBGE (https://servicodados.ibge.gov.br/api/v1/paises).
- Gerado em: 2026-11-02 (27 UFs, 5571 municípios, 193 países).
- Como atualizar: `python scripts/gerar_localidades.py` e depois reconstruir o site. A página do visitante nunca chama o IBGE.
- Formato: `states.json` = [sigla, nome, código IBGE da UF]; `municipalities/{UF}.json` = [código IBGE (7 dígitos), nome]; `countries.json` = [ISO 3166-1 alfa-2, nome em português].
- `google-apps-script/Municipios.gs` é gerado junto: é a tabela que o servidor usa para conferir UF, município e país.
