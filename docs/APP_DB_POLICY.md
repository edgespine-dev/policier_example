# APP_DB_POLICY

Detta är en generell app->DB-policy. Policier används som konkret exempel på namn, variabler och wiring.

## Goal
`policier` ska använda en dedikerad read/write-användare och får inte återanvända klusterövergripande postgres-adminuppgifter.

## Secret Contract (UNS)
- OpenBao KV mount: `kv`
- Credential path: `<overlay>/agents/policier/db/creds`
- Keys:
  - `POLICIER_DB_NAME`
  - `POLICIER_DB_USER`
  - `POLICIER_DB_PASSWORD`

Exempel:
- `kv/dev/agents/policier/db/creds`
- `kv/prod/agents/policier/db/creds`

## Runtime Wiring
- Credentials levereras via ExternalSecret `policier-db-creds`.
- DB endpoint levereras via ConfigMap `policier-db-config`.
- Default endpoint:
  - `postgres.infra-postgres.svc.cluster.local:5432`

Miljövariabler i runtime:
- `POLICIER_DB_HOST`
- `POLICIER_DB_PORT`
- `POLICIER_DB_NAME`
- `POLICIER_DB_USER`
- `POLICIER_DB_PASSWORD`
- `POLICIER_DB_SSLMODE`

## Bootstrap Flow (concrete example)
Kör DB-bootstrap för dev:

```bash
bootstrap/500_policier_db_create.sh --overlay dev
```

Beteende:
- Idempotent som default.
- Återanvänder existerande `POLICIER_DB_*` om de redan finns.
- Säkerställer role/database/grants i PostgreSQL.

Lösenordsrotation:

```bash
bootstrap/500_policier_db_create.sh --overlay dev --force
```

## Security Guardrails
- Använd dedikerad app-user (default: `policier_rw`).
- Använd dedikerad app-DB (default: `policier`).
- Montera inte root/admin-postgres-credentials i appen.
- Lagra aldrig plaintext-credentials i Git.

## How to reuse this for another app
Behåll exakt samma mönster, men byt prefix:
- `POLICIER_DB_*` -> `<APP>_DB_*`
- `<overlay>/agents/policier/db/creds` -> `<overlay>/agents/<app>/db/creds`
- `policier-db-creds`/`policier-db-config` -> `<app>-db-creds`/`<app>-db-config`

Policier-namnen i detta dokument är alltså ett konkret exempel på det generella app->DB-mönstret.
