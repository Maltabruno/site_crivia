# Google Drive — estrutura prevista (não criada)

Pasta raiz sugerida: **CRIVIA — Captação de Cenários do Site**, na conta institucional (`{{GOOGLE_ACCOUNT_OWNER}}`).

```text
01 Base de cenários        (planilha "CRIVIA — Cenários recebidos pelo site")
02 Documentos recebidos    (vazio e SEM uso: upload desligado)
03 Governança LGPD         (mapa de tratamento, checklist, decisões)
04 Relatórios e indicadores
05 Backups controlados
```

Regras: acesso restrito a pessoas autorizadas; nenhum link público, nada publicado na web; não compartilhar senha; revisar acessos periodicamente;
sem cópias desnecessárias; nunca usar o nome do visitante em pasta ou arquivo (usar o código público `CRV-AAAA-XXXXXX`).
**Interromper e informar o risco** se a pasta estiver dentro de outra com permissões amplas.
Nesta versão o Apps Script **não usa o Drive** (`DRIVE_ROOT_FOLDER_ID` e `SECURE_UPLOAD_FOLDER_ID` ficam vazios; `SECURE_UPLOAD_ENABLED=false`).
Pré-requisitos do upload futuro (token temporário, expiração, allowlist e validação de tipo/assinatura, limite de tamanho, renomeação, quarentena, retenção, exclusão, registro de acesso; bloquear executáveis, scripts, HTML, SVG não sanitizado, macros, compactados, extensões duplas): ver `security-threat-model.md`.
