# Student Analytics: Project Plan

Course: Sistemet e procesimit të të dhënave Dizajnuese (Prof. Dr. Sc. Liridon Hoti)
Deadline: **2027-01-08** (late submission means no right to defend). Plan written 2026-11-07, about 9 weeks left.
Submission: source code + presentation, submitted by one group member. Every member must attend the defence.

## 1. Where we are

| Requirement (PDF section) | Status |
|---|---|
| 2.1 Problem and requirements | Not written |
| 2.2 Architecture | Partial: FastAPI + PostgreSQL + Redis + React chosen, no document or diagrams |
| 2.3 Data model | Only `users` table. OULAD CSVs downloaded and documented (`data/README.md`), nothing loaded |
| 2.4 Data processing (core) | Not started |
| 2.5 API | Auth only: register, login, logout, me, users, health |
| 2.6 Security | Mostly done for auth: argon2, JWT with jti denylist, login rate limit, roles, env-based secrets, parameterised queries via SQLAlchemy |
| 2.7 Performance | Not started |
| 2.8 Testing | 9 auth/health tests. No evidence report |
| 2.9 Analytics / ML | Not started. Dashboard is a placeholder |
| 2.10 Deployment | Backend Dockerfile + compose (api, db, redis) + Alembic. No frontend container, no CI/CD, no K8s |

Repo: monorepo `vesab0/student-analytics` with `backend/` and `frontend/`.

Frontend: Vite + React 19 + TS with login, register, protected routes, admin page, empty dashboard.

Known issues to fix early:
- `ADMIN_PASSWORD` defaults to `admin123`. Remove the default so startup fails without it.
- The default admin is documented in the README. Drop that line.
- `.env` is git-ignored and was never committed (verified when merging the repos).

## 2. Decisions to make now

The PDF contradicts itself on advanced tech. It says Spark/Kafka "must be used" and CI/CD + Kubernetes are "universal requirements", but also says tech must be chosen by need and any exception from the minimum needs written justification and approval from the professor.

Recommended stance:

| Tech | Decision | Reason |
|---|---|---|
| Docker / Compose | Use | Already in place |
| Git + GitHub Actions CI | Use | Cheap, required |
| Apache Spark | Use (PySpark batch ETL) | `studentVle.csv` is 10.6M rows (~460 MB), a real justification, and the PDF asks for it |
| ML model | Use (dropout/pass-fail prediction) | PDF says ML/classification must be included |
| Kafka | Small stream demo only if time allows, otherwise ask for exemption | Dataset is historical batch data. Streaming has weak justification |
| Kubernetes | Minimal manifests run on kind/minikube, or ask for exemption | Listed as universal but contradicts section 7 |

**Action: email the professor this week** with the Kafka and Kubernetes position and get approval in writing. Do not leave it for the defence.

Also decide: team members and who owns what (the defence checks individual contribution), and which dataset subset to use if the full 10M-row table is too slow on laptops.

## 3. Target architecture

```
OULAD CSVs --> Spark ETL (validate, dedupe, aggregate) --> PostgreSQL (normalised + feature tables)
                                                               |
                                    FastAPI (JWT, RBAC, Redis cache/rate limit) <--> ML model (scikit-learn)
                                                               |
                                                   React dashboard (charts, filters, predictions)
```

Layers: UI (React), business logic (FastAPI services), data (PostgreSQL via SQLAlchemy/Alembic), processing (Spark jobs), cache/session (Redis).

Roles:
- **student**: sees own risk score and activity
- **lecturer**: sees courses and cohorts, at-risk lists
- **admin**: manages users, triggers ETL

Link OULAD `id_student` to `users` through a nullable `users.student_id` or a separate `students` mapping, so a logged-in student sees only their own data.

## 4. Steps to completion

Week numbers count from 2026-11-09.

### Phase 0: Housekeeping (week 1)
1. Fix the known issues above. (Monorepo done: `frontend/` and `backend/` in one repo.)
2. Send the exemption/approval email to the professor.
3. Create `docs/` and start a running decision log (needed for the "justify a technical decision" part of the defence).
4. Pin versions in one place (backend `requirements.txt`, frontend `package.json`, Docker image tags).

### Phase 1: Requirements and analysis (week 1-2) [2.1]
5. Write `docs/requirements.md`: problem statement (early identification of at-risk students), objectives, actors and roles.
6. List at least 5 functional requirements, each with an ID and an acceptance test. Suggested:
   - FR1 import and validate OULAD data
   - FR2 view course and student performance statistics with filters
   - FR3 view engagement trends from VLE clicks
   - FR4 predict at-risk students and show the result
   - FR5 role-based access to data
   - FR6 user management by admin
   - FR7 CRUD on a domain entity (see phase 3)
7. List non-functional requirements with measurable targets: security (argon2, JWT, rate limit), performance (e.g. dashboard queries under 500 ms p95), reliability (health checks, restart policy), maintainability (tests, migrations, lint).
8. Add a requirement-to-test traceability table. It is reused in the testing report.

### Phase 2: Architecture document (week 2) [2.2]
9. Write `docs/architecture.md` with component diagram, data-flow diagram (source to dashboard), deployment diagram, and the reasoning for a layered monolith plus a batch Spark job over microservices.
10. Document the limits of the system and the scaling options (stateless API behind a load balancer, read replicas, partitioning the clicks table).

### Phase 3: Data model and loading (week 2-4) [2.3]
11. Design the schema from OULAD: `courses` (module + presentation), `assessments`, `vle` (materials), `students` (studentInfo), `registrations`, `student_assessments`, `student_vle` (clicks). Add primary/foreign keys, CHECK and NOT NULL constraints, enums for result/gender/age band.
12. Normalise (3NF) and write down what was changed against the raw CSVs. OULAD is mostly normalised already, so the main work is typing, nulls and splitting repeated course columns.
13. Create Alembic migrations 0002+ for the schema.
14. Add the indexes the queries will need (for example `student_vle(id_student, date)`, `student_vle(code_module, code_presentation)`). Record each index with the query that justifies it (needed for 2.7).
15. Decide the CRUD demo entity (suggested: lecturer-managed `interventions` or `notes` on a student, or admin-managed courses) with full Create/Read/Update/Delete through the API.
16. Seed script for small test data, separate from the full load.
17. Update `data/README.md` with source, format, volume and preparation steps (already partly done).

### Phase 4: ETL with Spark (week 3-5) [2.4, core]
18. Add a Spark service to Docker Compose (or run PySpark in a job container).
19. Extract: read the 7 CSVs with explicit schemas.
20. Validate and clean: nulls (e.g. missing `imd_band`, `date` in registration), duplicates, out-of-range values, orphan foreign keys. Write rejected rows to a quarantine table or file with the reason.
21. Transform and aggregate: per-student, per-course features (total clicks, active days, clicks by activity type, early-window clicks, weighted assessment score, submission lateness, number of attempts).
22. Load: write cleaned tables and the feature table into PostgreSQL via JDBC.
23. Make the job idempotent and repeatable (truncate-and-load or upsert), with logging of row counts in/out/rejected.
24. Produce an ETL run report (counts, timings) to show at the defence.
25. Optional streaming demo: replay `studentVle` rows through Kafka into a rolling-clicks table. Only if the professor requires Kafka and time remains.

### Phase 5: Analytics API (week 4-6) [2.5, 2.9]
26. Add routers and services, keeping the existing layering (`api` -> `schemas` -> `models`):
    - `GET /courses`, `GET /courses/{id}/stats` (pass rate, withdrawal rate, mean score)
    - `GET /students/{id}/summary` (student: own only; lecturer/admin: any)
    - `GET /analytics/engagement` with filters (module, presentation, date range, demographics)
    - `GET /analytics/at-risk` (lecturer/admin)
    - CRUD endpoints for the chosen entity
    - `POST /admin/etl/run` (admin) if triggering from the API is practical
27. Pagination, filtering and input validation (Pydantic), consistent error format, no internal details in errors.
28. Authorisation per endpoint using the existing `require_role`, plus row-level checks for students.
29. Redis cache for expensive aggregate endpoints, with TTL and invalidation after ETL.
30. Keep OpenAPI docs accurate. They double as the API specification for the report.

### Phase 6: Machine learning (week 5-7) [2.9]
31. Define the target: `final_result` collapsed to at-risk (Fail, Withdrawn) vs not, predicted using only data available up to a cutoff (e.g. first 60-90 days) to avoid leakage.
32. Train baseline (logistic regression) and a stronger model (random forest or gradient boosting) with scikit-learn. Use a proper train/test split, grouped by student if they appear in several presentations.
33. Report accuracy, precision/recall, F1, ROC-AUC and a confusion matrix. State the limitations honestly (class imbalance, dataset age, demographic bias, one university).
34. Persist the model artefact and version it. Serve predictions through the API and store them in a `predictions` table.
35. Results must be real and reproducible: fixed random seed, script in the repo, numbers in the report taken from actual runs.

### Phase 7: Frontend (week 5-8) [2.9]
36. Install a chart library (Recharts or similar) and a small data-fetching approach consistent with `src/api/client.ts`.
37. Pages: dashboard overview (KPIs), course explorer with filters, engagement charts, at-risk table with risk scores, student detail (own view for students), admin (users, ETL status, CRUD entity).
38. Show explanations of each result and its limits on the page, as the PDF asks.
39. Loading, empty and error states. Role-aware navigation.
40. Add a frontend service to Docker Compose (nginx serving the Vite build, proxying `/api`).

### Phase 8: Security hardening (week 6-7) [2.6]
41. Remove default admin password, require strong secrets at startup, confirm no secrets in git history.
42. CORS locked to the frontend origin, security headers, request size limits.
43. Run a short threat review (OWASP top 10 mapping) and write `docs/security.md`: risks, mitigations, evidence (tests).
44. Add tests that demonstrate SQL injection attempts are neutralised and unauthorised access is blocked (403/401 matrix across all endpoints).
45. Consider refresh tokens or shorter expiry, and token storage on the frontend (avoid localStorage if feasible, otherwise document the trade-off).

### Phase 9: Performance (week 7-8) [2.7]
46. Pick a representative slow query (e.g. clicks per module per week).
47. Measure it before: `EXPLAIN (ANALYZE, BUFFERS)` and timing over repeated runs.
48. Optimise (index, pre-aggregated table or materialised view, query rewrite), measure after, record before/after numbers.
49. Measure cache hit vs miss latency, and one API load test (e.g. `locust` or `k6`) at several concurrency levels. Report throughput and p95.
50. Write down the bottlenecks (Spark JDBC write, single Postgres, Argon2 CPU cost on login) and scaling options. Do not claim scalability without these measurements.

### Phase 10: Testing (continuous; formal pass week 8-9) [2.8]
51. Backend unit and integration tests: ETL validation rules (valid, invalid, duplicate, boundary rows), every endpoint (success, validation error, auth error), CRUD round-trip, ML pipeline sanity.
52. Frontend: at minimum a few component/route tests (Vitest + Testing Library), or a documented manual test script with results.
53. Test case table in `docs/testing.md`: ID, requirement, input, expected, actual, status. Include defects found and how they were fixed.
54. Save evidence: pytest output, coverage report, screenshots.

### Phase 11: Deployment and CI/CD (week 7-9) [2.10]
55. One `docker compose up` brings up db, redis, api, spark job, frontend. Document it in the root README with exact versions.
56. GitHub Actions: lint (oxlint, ruff), type check, backend tests with service containers, frontend build, Docker image build.
57. Kubernetes (if not exempted): manifests or Helm chart for api, frontend, postgres, redis, applied on kind/minikube; show it running. Keep it small.
58. `.env.example` complete and accurate.

### Phase 12: Documentation and presentation (week 9)
59. Root `README.md`: purpose, architecture picture, prerequisites, run steps, test steps, repo layout.
60. Consolidate `docs/`: requirements, architecture, data model (ER diagram), ETL, API, security, performance, testing, AI-use and sources statement (dataset citation, libraries, AI tool use per course rules).
61. Presentation: problem, solution, technologies and why, results (ETL numbers, model metrics, performance before/after), limitations.
62. Add an individual contribution log per member from git history.

### Phase 13: Defence rehearsal (week 9, before 2026-12-31)
63. Dry run from a clean clone on a fresh machine: `docker compose up`, load data, log in as each role.
64. Prepare the demo script: system running, data flow source to dashboard, DB and processing internals, 3+ test cases, one technical decision with justification.
65. Practise live changes the professor may ask for: add a field, change a filter, fix a validation, write a new SQL query. Everyone must be able to explain every part of the code they own.
66. Freeze the code a few days before **2027-01-08** and submit early.

## 5. Suggested timeline

| Week (start) | Focus |
|---|---|
| 1 (Nov 9) | Phase 0, start phase 1 |
| 2 (Nov 16) | Phases 1-2, start phase 3 |
| 3 (Nov 23) | Finish schema + migrations, start Spark ETL |
| 4 (Nov 30) | ETL complete, start API |
| 5 (Dec 7) | Analytics API, start ML and frontend charts |
| 6 (Dec 14) | ML, frontend pages, security hardening |
| 7 (Dec 21) | Performance measurements, CI, Docker for frontend |
| 8 (Dec 28) | Testing pass, Kubernetes, fixes |
| 9 (Jan 4) | Docs, presentation, rehearsal, submit by Jan 8 |

The load-bearing items are the data model, the ETL, and the ML result. If time runs short, cut Kafka, Kubernetes and extra dashboard pages first, with the professor's approval.

## 6. Grading checklist (section 4 of the PDF)

Weights are blank in the PDF (total 40%). Each category needs visible evidence:

- [ ] Problem analysis and requirements: `docs/requirements.md`
- [ ] Architecture and design: `docs/architecture.md` with diagrams
- [ ] Data modelling and management: schema, migrations, seed data, CRUD demo
- [ ] Data processing: Spark ETL with validation, aggregation, run report
- [ ] Security and integrity: `docs/security.md`, authz tests
- [ ] Testing and verification: `docs/testing.md` with evidence
- [ ] Performance and optimisation: before/after measurements
- [ ] Technical documentation and reproducibility: README, pinned versions, one-command run
- [ ] Practical demo and individual defence: rehearsed script, per-member contributions
