# Java Job Intelligence Platform

Production-grade full-stack application for daily discovery, aggregation, deduplication, analytics, and Excel export of Java Developer jobs in India for 2-5 years experience.

## Features

- Clean Architecture backend: routes, controllers, services, repositories, models, middleware, validators, jobs, schedulers, queues, integrations, config, constants, database, tests.
- MongoDB schemas for Company, Job, and JobHistory.
- Pluggable provider adapters implementing `JobProvider.fetchJobs()` for Google, Microsoft, Amazon, Oracle, and JPMorgan Chase, with an extensible company registry.
- Java/Spring Boot/Microservices/Kafka/Redis/SQL/Cloud/Docker/Kubernetes matching rules.
- Rejects internships, managers, architects, directors, and out-of-band experience roles.
- Deduplicates by unique `(companyId, jobId)` and by title/location/apply URL.
- Daily schedule at 06:00 AM IST through `node-cron`; BullMQ/Redis backed sync queue.
- Dashboard with total jobs, jobs by company/city/experience, recently added jobs, top hiring companies, search, filters, AG Grid, and Excel export.
- Swagger UI at `/api/docs`, OpenAPI spec in `docs/openapi.yaml`.
- Docker Compose, env templates, unit/integration tests, and GitHub Actions CI.

## Quick Start

```bash
cd java_job_intelligence
cp .env.example .env
npm install
npm run dev
```

- Backend: http://localhost:4000
- Frontend: http://localhost:5173
- Swagger: http://localhost:4000/api/docs

## Docker

```bash
cd java_job_intelligence
cp .env.example .env
docker compose up --build
```

## API

- `GET /api/jobs`
- `GET /api/jobs/:id`
- `GET /api/companies`
- `GET /api/stats`
- `GET /api/export/excel`
- `POST /api/sync`

`POST /api/sync` is JWT protected in production and open in development/test.

## Extending Providers

1. Add or update company metadata in `backend/src/constants/companyRegistry.ts`.
2. Implement a provider in `backend/src/integrations/providers` that returns normalized `ProviderJobInput[]`.
3. Register it in `ProviderFactory.createProviders()`.
4. Add endpoint credentials through environment variables or a secrets manager.

The included adapters support configurable career API endpoints and deterministic seed fallback data for local development.

## Tests and Checks

```bash
npm run typecheck
npm run test
npm run build
```

Integration tests use `mongodb-memory-server`.

## Excel Export

`GET /api/export/excel` returns `java-jobs-yyyy-mm-dd.xlsx` with:
Company, Job ID, Job Title, Location, Experience, Skills, Posted Date, Apply URL, Source, Description.

## Production Notes

- Replace Mongo credentials and `JWT_SECRET`.
- Run queue workers separately from API replicas for larger sync volume.
- Configure real provider endpoints and comply with provider terms of service.
- Add centralized logging, Mongo backups, alerting, and secret management before internet-facing deployment.
