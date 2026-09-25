# SHIFT Backend

## Status: Beta-complete

Every module listed as mandatory for the beta in the original spec is implemented,
wired together, and tested end-to-end against a real PostgreSQL 16 instance and a
running FastAPI app — not just unit-tested in isolation. This document reflects
what is actually in this codebase today, not what's planned.

| Module | Status |
|---|---|
| Auth (JWT login/refresh) | Done |
| Users & OC hierarchy (PM → OCP → OCVP → OC) | Done |
| Permission framework (role → action matrix) | Done |
| Partner CRM (search, create, edit, status, history) | Done |
| **Already-contacted duplicate block** (target lists) | Done — see below |
| Partner contact log & official collaborations | Done |
| Partner bulk import (CSV/XLSX, preview → commit) | Done |
| Target Lists & items | Done |
| Speakers (mirrors partner dedup logic) | Done |
| Tasks (hierarchy-enforced assignment) | Done |
| Goals (with auto-derived status) | Done |
| MKT Timeline | Done |
| Dashboards (me / team / project / admin) | Done |
| Activity log (audit trail) + viewing endpoint | Done |
| Global search (partners, speakers, users, target lists) | Done |
| Projects & Departments (reference data endpoints) | Done |
| **Not built:** Notifications, email/follow-up integration, Google Sheets sync | Explicitly deferred per spec (optional for beta) |
| **Not built:** Frontend | Out of scope for this pass — backend only |

## Quick setup

1. Create the database:
   ```sql
   CREATE DATABASE shift_db;
   CREATE USER shift_user WITH PASSWORD 'shift_password';
   GRANT ALL PRIVILEGES ON DATABASE shift_db TO shift_user;
   ```
2. `cp .env.example .env` and edit `DATABASE_URL`, `SECRET_KEY`, and `SEED_ADMIN_*`
   (change the seed password before running in anything but a scratch environment).
3. `pip install -r requirements.txt` (or `requirements-dev.txt` to also get pytest/httpx).
4. `alembic upgrade head` — creates all 17 tables and their Postgres enum types.
5. `python -m scripts.seed_initial_data` — creates the SHIFT project, five default
   departments (BD, MKT, Logistics, Finance, Corporate — all editable afterwards),
   and the first Admin account. Refuses to run again once an Admin exists.
6. `uvicorn app.main:app --reload` — API docs at `http://localhost:8000/docs`.

## Architecture

```
Router (app/routers/*)          -- validates request shape, calls a service,
                                    translates service errors to HTTP status codes
     |
Service (app/services/*)        -- business rules: dedup detection, hierarchy
                                    validation, permission-aware logic, activity logging
     |
Repository (app/repositories/*) -- plain SQLAlchemy queries, no business logic
     |
Model (app/models/*)            -- ORM mapping + DB-level constraints (uniqueness,
                                    FKs, native Postgres enums)
```

`app/core/permissions.py` holds the entire role→action matrix in one dict.
`app/services/hierarchy_service.py` is the single source of truth for who can
report to whom, and is reused by both user creation and task assignment.

## The core feature: server-side duplicate-contact blocking

This is the feature the spec calls "mandatory" and "the most important
database/backend rule," so it gets its own section.

**The rule:** once a partner has been contacted by anyone (status moves past
`NEW`), no one else can add that same company to a *different* target list as
a fresh, untouched prospect. The block is enforced in
`app/services/partner_service.py::get_or_create_partner_for_target_list`,
called from `app/services/target_list_service.py::add_item` — never in the
API layer alone, and never assumed to have been checked by a client.

**How it's actually enforced, end to end:**
1. Company names are matched via `normalize_company_name()` (lowercase, strip
   punctuation, collapse whitespace) against `partners.normalized_name`, which
   carries a `UNIQUE` constraint at the database level — so even a race
   condition or a buggy caller can't create two records for "XYZ Company" and
   "xyz   company!!".
2. If a match exists and its status is anything past `NEW`, the request is
   rejected with **HTTP 409**, carrying the full history (last contact, who,
   when, notes) in the response body — the shape the spec's warning panel
   describes exactly.
3. The one-time exception — overriding the block — is **only** honored if the
   *actor's role* carries `PARTNER_OVERRIDE_BLOCK` (Admin, in this beta), and
   that check happens server-side regardless of what the request body claims.
   A non-admin setting `override_duplicate_block: true` has zero effect.
4. Adding the *same* partner twice to the *same* list is checked and rejected
   with a separate, more specific 400 error before the global block logic
   even runs (this ordering was a real bug caught during testing — see below).

This was tested with two different users, different casing/spacing/punctuation
in the company name, an override attempt by a non-admin (rejected) and by an
Admin (allowed), and confirmed the block information matches what the other
user actually logged.

## What's enforced at the database level (not just in the API)

- `partners.normalized_name`, `speakers.normalized_name`, `users.email` — all `UNIQUE`.
- `target_list_items(target_list_id, partner_id)` — `UNIQUE`, so a partner can't
  be added twice to the same list even if application logic is bypassed.
- Every status/role/priority/type column is a native Postgres `ENUM` — an
  invalid value is rejected by the database itself, not just by Pydantic.
- Foreign keys carry explicit `ON DELETE` behavior (`CASCADE` for owned child
  data like contacts and list items, `SET NULL` for references that should
  survive the referenced row's deletion).

## Business rules enforced server-side (never assumed from the frontend)

- **Task assignment hierarchy:** `create_task` (in `task_service.py`) checks
  `is_direct_report()` — a manager can only assign to someone whose
  `manager_id` points at them. Admin can assign to anyone. Verified: OCP→OCVP
  allowed, OC→anyone forbidden (OC has no `TASK_CREATE` permission at all),
  and an OCVP trying to assign to a peer OCVP forbidden.
- **Task status updates:** only the assignee or an Admin can change a task's
  status — a manager who created a task can't mark someone else's work "done."
- **Partner official-field edits / status changes:** gated by
  `PARTNER_EDIT_OFFICIAL` / `PARTNER_CHANGE_STATUS`, held by OCVP+ and Admin
  only — ordinary OC members can log a contact but never touch official state.
- **Partner import:** Admin-only (`PARTNER_IMPORT`), and duplicates (both
  against the existing database and *within* the uploaded file) are tagged and
  skipped at commit time — never silently created.
- **User/hierarchy management:** Admin-only. Creating or re-assigning a user
  validates the manager/role pairing (`hierarchy_service.py`) — e.g. an OCP's
  manager must be a PM, not another OCP.

## API surface (42 routes)

```
POST   /auth/login                              POST   /auth/refresh

GET    /users                GET /users/me      POST   /users
PATCH  /users/{id}/manager   PATCH /users/{id}/deactivate

GET    /projects             POST /projects
GET    /departments          POST /departments

GET    /partners              POST /partners     GET /partners/search
GET    /partners/{id}         PUT  /partners/{id}
PATCH  /partners/{id}/status
GET    /partners/{id}/history
POST   /partners/{id}/contacts
POST   /partners/{id}/collaborations

POST   /partners/import
GET    /partners/import/{batch_id}/preview
POST   /partners/import/{batch_id}/commit

GET    /target-lists          POST /target-lists
GET    /target-lists/{id}
GET    /target-lists/{id}/items       POST /target-lists/{id}/items
PATCH  /target-lists/items/{item_id}/status

GET    /speakers              POST /speakers     GET /speakers/search
GET    /speakers/{id}         PUT  /speakers/{id}
PATCH  /speakers/{id}/status
GET    /speakers/{id}/history
POST   /speakers/{id}/contacts

GET    /tasks?scope=mine|created|team
GET    /tasks/counts/me
POST   /tasks
PATCH  /tasks/{id}/status

GET    /goals?project_id=...  POST /goals
PATCH  /goals/{id}/progress

GET    /mkt-timeline?project_id=...   POST /mkt-timeline
PATCH  /mkt-timeline/{id}/status

GET    /dashboard/me          GET /dashboard/team
GET    /dashboard/project     GET /dashboard/admin

GET    /activity-logs
GET    /search?q=...

GET    /health
```

## What's verified end-to-end (real Postgres + real HTTP requests, not mocks)

Across the full build, this includes (non-exhaustive):
- Login, JWT validation, token refresh, deactivated-account lockout.
- Full PM → OCP → OCVP → OC chain creation, with invalid pairings rejected
  server-side with a clear message (not just a generic 400).
- The complete "already contacted" workflow described above, including the
  same-list-duplicate ordering bug found and fixed during testing.
- Task hierarchy enforcement matching the spec's explicit test scenarios
  (OCP→OCVP allowed, OC forbidden from creating tasks, peer-to-peer OCVP
  assignment forbidden, Admin override allowed).
- Speaker dedup mirroring the partner logic exactly.
- Goal progress auto-deriving `ACHIEVED` at 100% of target.
- MKT timeline rejecting an end date before its start date.
- Dashboard numbers coming from live `COUNT`/`GROUP BY` queries, not fixtures.
- Partner import: CSV and XLSX uploads, exact new/duplicate/error counts in
  the preview, in-file duplicates caught (not just DB duplicates), invalid
  email and invalid `partner_type` values rejected with specific messages,
  nothing written to the database until `/commit`, double-commit rejected,
  and a non-admin blocked from importing at all.
- Global search matching partners/speakers by normalized name and users/lists
  by substring.

Two real bugs were found and fixed during this testing (not just noted as
risks): an enum-type double-creation error in the initial Alembic migration,
and an ordering bug where the "already on this list" check ran after — instead
of before — the global duplicate-contact block, producing a confusing error
when a user tried to re-add their own already-contacted item to the same list.

## Known simplifications (beta-appropriate, not hidden)

- **Overdue tasks:** `/tasks/counts/me` computes "overdue" dynamically by
  comparing `deadline` to now; `/dashboard/project`'s task breakdown reflects
  the stored `OVERDUE` enum value only, which nothing currently sets — there's
  no background sweep job yet. The two will disagree until one is added.
- **Department-scoped partner edits:** the permission matrix grants
  `PARTNER_EDIT_OFFICIAL` to all OCVPs platform-wide, not scoped to "their own
  department's partners" — the Phase 1 doc flagged this as an open question
  and this beta took the simpler platform-wide option.
- **Notifications, email/follow-up, Google Sheets import:** explicitly marked
  optional/deferred in the spec and not built. The import architecture
  (`partner_import_service.py` takes a filename + bytes and returns normalized
  rows) is source-agnostic, so a future Google Sheets importer can plug into
  the same `validate_and_stage_rows` / `commit_import` pipeline without
  reworking the Partner module.

## Next steps

The backend is feature-complete for the beta scope. Remaining work is either
explicitly-deferred (notifications, email), or frontend (not part of this pass).
