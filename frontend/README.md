# SHIFT Frontend V2

Production-oriented React + TypeScript frontend aligned to `backend(2).zip`.

## Stack
React, TypeScript, Vite, React Router, TanStack Query, Axios, Framer Motion, Lucide React.

## Run
```bash
npm install
cp .env.example .env
npm run dev
```
Set `VITE_API_URL` to the FastAPI base URL.

## Implemented backend contract
- Auth: login, refresh, `/users/me`
- Dashboard: me, team, project/admin dashboard surfaces
- Users: list/create/manager/deactivate
- Projects and project departments
- Partner registry, search, edit, status, contacts, collaborations, history
- Target lists, item management, duplicate-contact 409 UX and admin override
- Speakers, search, edit, status, contacts, history
- Tasks, counts, mine/created/team scopes, status changes
- Goals and progress-ready architecture
- MKT timeline and status changes
- Activity log
- Global search
- Partner CSV/Excel import preview + commit
- Registration page prepared for the planned future `/auth/register` endpoint

## Security notes
The frontend treats RBAC as a UX layer only. Authorization remains server-side. Access tokens are held in session storage for this backend contract; the backend currently accepts refresh tokens in JSON, so an HttpOnly-cookie refresh flow would be the preferred future hardening.
