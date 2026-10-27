# Vehicle Job Tracker — REST API (v1)

Part 1 is for **developers integrating with the API** (the external team).
Part 2 is for **maintainers** of this project.

---

# Part 1 — Using the API

## Base URL

```
https://<server-domain>/api/v1
```

Your administrator gives you the exact domain. All requests and responses are JSON.

**Interactive docs:** open `https://<server-domain>/api/v1/docs` in a browser, click
**Authorize**, paste your API key, and you can try every endpoint from the page.
The machine-readable OpenAPI spec is at `/api/v1/openapi.json` — you can import it
into Postman / Insomnia, or generate a client library in any language from it
(see [Generating a client](#generating-a-client-in-any-language)).

## Authentication

Every request must send your API key in the `X-API-Key` header:

```
X-API-Key: vjt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

A missing, wrong, or revoked key returns `401 Unauthorized`.

Keep the key secret, like a password:

- Store it in an environment variable or secrets manager — never in source code or git.
- Call the API **from your backend only.** Never put the key in browser JavaScript or a
  mobile app, where anyone can read it.
- If you think the key has leaked, tell the administrators immediately — they will
  revoke it and issue a new one.

## Endpoints at a glance

| Method | Path | What it does |
|---|---|---|
| `GET` | `/users` | List users (search, filter, paginate) |
| `GET` | `/users/{id}` | Get one user by id |
| `GET` | `/users/by-username/{username}` | Get one user by username |
| `POST` | `/users` | Create a user |
| `PATCH` | `/users/{id}` | Change a user's details |
| `GET` | `/jobs` | List jobs (id, location, date, creator) |
| `GET` | `/jobs/{id}` | Get one job |
| `PATCH` | `/jobs/{id}` | Change a job's location |

---

## Users

### The user object

```json
{
  "id": 12,
  "username": "ali.khan",
  "full_name": "Ali Khan",
  "role": "user",
  "is_active": true,
  "is_approved": true,
  "companies": ["DHL PAK"],
  "created_at": "2026-10-27T09:15:02.123456"
}
```

| Field | Meaning |
|---|---|
| `role` | `user` (add/edit jobs), `field_support` (add/edit/delete jobs), `viewer` (read only). Admin roles also appear in responses, but the API can't assign them. |
| `is_active` | `false` = the account is deactivated and can't sign in. |
| `companies` | Companies the user is limited to in the web app. **Empty list = all companies.** |
| `created_at` | UTC timestamp. |

Passwords are never returned.

### List users — `GET /users`

| Query param | Type | Description |
|---|---|---|
| `q` | string | Partial match on username or full name (case-insensitive) |
| `role` | string | Exact role, e.g. `viewer` |
| `is_active` | bool | `true` / `false` |
| `page` | int | Page number, starts at 1 (default 1) |
| `page_size` | int | 1–200 (default 50) |

Response:

```json
{ "items": [ { ...user... } ], "total": 37, "page": 1, "page_size": 50 }
```

### Get a user — `GET /users/{id}` or `GET /users/by-username/{username}`

Returns the user object, or `404` if it doesn't exist.

### Create a user — `POST /users`

```json
{
  "username": "ali.khan",
  "full_name": "Ali Khan",
  "password": "S3cure-pass",
  "role": "user",
  "companies": ["DHL PAK"]
}
```

| Field | Required | Rules |
|---|---|---|
| `username` | yes | Max 80 chars. Stored lowercase and trimmed. Must be unique. |
| `password` | yes | 6–128 characters. |
| `full_name` | no | Max 150 chars. |
| `role` | no | `user` (default), `field_support`, or `viewer`. |
| `companies` | no | Must be from the [company list](#valid-company-names). Default `[]` (all companies). |

Returns `201 Created` with the new user. The account is approved and can sign in to the
web app straight away. A taken username returns `409 Conflict`.

### Update a user — `PATCH /users/{id}`

Send **only the fields you want to change**:

```json
{ "full_name": "Ali Raza Khan", "is_active": false }
```

| Field | Notes |
|---|---|
| `full_name` | Max 150 chars |
| `password` | Sets a new password (6–128 chars) |
| `role` | `user`, `field_support`, or `viewer` |
| `is_active` | `false` deactivates the account, `true` re-activates it |
| `companies` | **Replaces** the whole list. `[]` = all companies |

The username can't be changed. Administrator accounts (`admin`, `super_admin`) can't
be changed through the API; trying returns `403 Forbidden`.

---

## Jobs

### The job object

```json
{
  "id": 1045,
  "location": "Lahore",
  "date": "2026-10-05",
  "created_by": { "id": 12, "username": "ali.khan", "full_name": "Ali Khan" }
}
```

`date` is the job date (`YYYY-MM-DD`). `created_by` is `null` if the user who created
the job has since been deleted.

### List jobs — `GET /jobs`

Newest job date first, unless you set `sort`.

| Query param | Type | Description |
|---|---|---|
| `username` | string | Only jobs created by this user |
| `location` | string | Location contains this text (case-insensitive) |
| `date_from` | date | Job date on or after, `YYYY-MM-DD` |
| `date_to` | date | Job date on or before, `YYYY-MM-DD` |
| `sort` | string | `-date` (default, newest first), `date`, `id` (lowest id first), `-id` (highest id first) |
| `page` | int | Starts at 1 (default 1) |
| `page_size` | int | 1–200 (default 50) |

Response: `{ "items": [ ...jobs... ], "total": 812, "page": 1, "page_size": 50 }`

To fetch everything, keep requesting `page=1, 2, 3...` until you've collected `total`
items, or until a page comes back with fewer than `page_size` items.

### Get a job — `GET /jobs/{id}`

Returns the job object, or `404`.

### Change a job's location — `PATCH /jobs/{id}`

```json
{ "location": "Islamabad" }
```

`location` is required, 1–200 characters, and is trimmed. It's the only field this
endpoint can change; any other fields in the body are ignored. Returns the updated job.

---

## Errors

Error responses (except `500`) are JSON with a `detail` field:

```json
{ "detail": "User not found." }
```

| Status | Meaning |
|---|---|
| `422` | The request body or query is invalid. `detail` is a list saying which field failed and why. |
| `401` | Missing, invalid, or revoked API key |
| `403` | The key is valid, but the action isn't allowed (e.g. editing an admin account) |
| `404` | That user or job doesn't exist |
| `409` | Conflict, e.g. the username is already taken |
| `500` | Server error. Safe to retry `GET` requests; tell the administrators if it persists. |

An example `422`:

```json
{
  "detail": [
    { "loc": ["body", "password"], "msg": "String should have at least 6 characters", "type": "string_too_short" }
  ]
}
```

## Valid company names

`Unilever Trucks`, `Unilever Pool Cars`, `UPFL Pool Cars`, `Magnum Primary`,
`Magnum Secondary`, `Wall's Pool Cars`, `Emirates Logistics`, `Allied Logistics`,
`KKC Pvt Ltd`, `Nestle Dedicated`, `Nestle NON Dedicated`, `Go Petroleum`,
`DHL Global`, `Shaheen Fright`, `Engro Polymer`, `DHL PAK`

They're case-sensitive and must match exactly.

---

## Examples

### curl

```bash
export VJT_URL="https://<server-domain>/api/v1"
export VJT_API_KEY="vjt_..."

# List the jobs Ali created in October
curl -H "X-API-Key: $VJT_API_KEY" \
  "$VJT_URL/jobs?username=ali.khan&date_from=2026-10-01&date_to=2026-10-31"

# Create a user
curl -X POST "$VJT_URL/users" \
  -H "X-API-Key: $VJT_API_KEY" -H "Content-Type: application/json" \
  -d '{"username":"ali.khan","full_name":"Ali Khan","password":"S3cure-pass","role":"user"}'

# Deactivate a user
curl -X PATCH "$VJT_URL/users/12" \
  -H "X-API-Key: $VJT_API_KEY" -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Change a job's location
curl -X PATCH "$VJT_URL/jobs/1045" \
  -H "X-API-Key: $VJT_API_KEY" -H "Content-Type: application/json" \
  -d '{"location":"Islamabad"}'
```

### Python (`requests`)

```python
import os
import requests

BASE = os.environ["VJT_URL"]
session = requests.Session()
session.headers["X-API-Key"] = os.environ["VJT_API_KEY"]

# Create a user
r = session.post(f"{BASE}/users", json={
    "username": "ali.khan", "full_name": "Ali Khan",
    "password": "S3cure-pass", "role": "user",
}, timeout=15)
if r.status_code == 409:
    print("Username already exists")
r.raise_for_status()
user = r.json()

# Fetch all of that user's jobs, page by page
jobs, page = [], 1
while True:
    r = session.get(f"{BASE}/jobs", params={"username": user["username"], "page": page, "page_size": 200}, timeout=15)
    r.raise_for_status()
    data = r.json()
    jobs += data["items"]
    if len(jobs) >= data["total"] or not data["items"]:
        break
    page += 1

# Move a job
session.patch(f"{BASE}/jobs/{jobs[0]['id']}", json={"location": "Islamabad"}, timeout=15).raise_for_status()
```

### JavaScript / Node.js (18+, built-in `fetch`)

```js
const BASE = process.env.VJT_URL;
const headers = { "X-API-Key": process.env.VJT_API_KEY, "Content-Type": "application/json" };

async function api(method, path, body) {
  const res = await fetch(`${BASE}${path}`, { method, headers, body: body && JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(`${res.status}: ${JSON.stringify(data.detail)}`);
  return data;
}

const user = await api("POST", "/users", { username: "ali.khan", password: "S3cure-pass", role: "viewer" });
await api("PATCH", `/users/${user.id}`, { companies: ["DHL PAK"] });
const { items } = await api("GET", "/jobs?location=lahore&page_size=100");
await api("PATCH", `/jobs/${items[0].id}`, { location: "Lahore - DHA" });
```

### C# (.NET)

```csharp
var http = new HttpClient { BaseAddress = new Uri(Environment.GetEnvironmentVariable("VJT_URL") + "/") };
http.DefaultRequestHeaders.Add("X-API-Key", Environment.GetEnvironmentVariable("VJT_API_KEY"));

var jobs = await http.GetFromJsonAsync<JsonElement>("jobs?username=ali.khan");
var res = await http.PatchAsJsonAsync("jobs/1045", new { location = "Islamabad" });
res.EnsureSuccessStatusCode();
```

Any language with an HTTP client works the same way: send JSON and set the `X-API-Key` header.

### Generating a client in any language

The OpenAPI spec lets you generate a typed client instead of writing requests by hand:

```bash
# Example: generate a TypeScript client (Java, C#, Go, PHP, Python... are also supported)
npx @openapitools/openapi-generator-cli generate \
  -i https://<server-domain>/api/v1/openapi.json -g typescript-fetch -o ./vjt-client
```

Or in Postman: **Import → Link →** paste the `openapi.json` URL.

## Versioning promise

Everything under `/api/v1` stays backward compatible. We may **add** new endpoints,
optional request fields, or new response fields — so make your code ignore fields it
doesn't recognise. Renaming or removing fields, or changing their meaning, only happens
in a new version (`/api/v2`), and `v1` will keep running alongside it for a migration
period we'll agree with you.

---

# Part 2 — Maintaining the API

## How it's built

```
app/api/
├── __init__.py      # api_v1 FastAPI sub-app; mounted at /api/v1 in app/main.py
├── auth.py          # X-API-Key check (require_api_key), key generation + hashing
├── permissions.py   # which roles the API may assign (no admin roles)
├── schemas.py       # Pydantic request/response models = the public contract
├── users.py         # /users endpoints
└── jobs.py          # /jobs endpoints
scripts/manage_api_keys.py   # issue / list / revoke keys
```

- The API is a **separate FastAPI sub-application**, so `/api/v1/docs` shows only the API
  and not the web pages. It shares the database, models, and `app/choices.py` with the
  web app, so roles, company names, and length limits stay in one place.
- **Auth** uses API keys, not user logins. A key represents a client system (e.g. "Partner
  Team"), not a person. Keys are 256-bit random strings (`vjt_` + 43 chars). Only their
  SHA-256 hash is stored in the `api_keys` table, so a database leak doesn't expose
  usable keys. `last_used_at` is updated at most every 5 minutes.
- The response models (`UserOut`, `JobOut`) decide exactly which columns leave the
  server. The API never returns `password_hash` or job fields other than id, location,
  date, and creator.
- **Guardrails:** the API can't create, promote to, or edit `admin` / `super_admin`
  accounts. That stays in the Admin Panel with a logged-in human. That way a leaked key
  can't take over the system or lock out the admins.

## Managing API keys

Give **each external team or system its own key**, so you can see who is calling and
revoke one without affecting the others.

On the server (`/opt/apps/vehicle_job_tracker`):

```bash
# Issue a key: the plain key is printed ONCE, so copy it now
docker compose exec web python scripts/manage_api_keys.py create "Partner Team"

# See all keys, their status, and when they were last used
docker compose exec web python scripts/manage_api_keys.py list

# Revoke a key (takes effect immediately, no restart needed)
docker compose exec web python scripts/manage_api_keys.py revoke 3
```

The script creates the `api_keys` table automatically the first time it runs.

**Sending the key to the client:** use a one-time secret link or a password manager
share. Don't send it in plain email or chat.

**Rotating a key** (do this yearly, or whenever someone with access leaves): create a new
key → send it to the client → wait until they've switched over (`list` shows the old
key's `LAST USED` stop moving) → revoke the old key.

## Deploying

1. Merge to `main`. The GitHub Action pulls the code and runs `docker compose up -d --build`.
2. **First deploy only:** issue a key with the command above (this also creates the table).
3. Smoke test from your machine:
   ```bash
   curl -i https://<server-domain>/api/v1/jobs?page_size=1 -H "X-API-Key: vjt_..."
   ```

### Before giving the API to the external team

- **HTTPS is mandatory.** The API key travels in a header, so over plain `http://` anyone
  on the network path can read it. Put nginx (or Caddy) in front of the `web` container
  with a Let's Encrypt certificate, and expose only port 443.
- **Rate limiting:** add an nginx `limit_req` zone on `/api/` (e.g. 10 requests/second
  per IP, with a burst) to protect the server from a client bug that loops.
- **Logging:** nginx access logs plus `last_used_at` show who is calling. Ask each
  client for a contact person and an expected request volume.
- **Backups:** the API writes to the same database as the web app. Make sure `backup.sh`
  runs on a schedule before real data flows through it.

## Changing the API safely

**Non-breaking (fine in v1):** adding an endpoint, an optional request field, a response
field, or a filter.

**Breaking (needs v2):** renaming or removing a field, making an optional field required,
changing a type or meaning, or changing an error code that clients handle.

To add v2 later: copy `app/api/` to `app/api_v2/`, change what you need, and mount it in
`app/main.py` with `app.mount("/api/v2", api_v2)`. Keep v1 running, give clients a
deadline, and remove v1 once its keys' `last_used_at` stops moving.

**Adding an endpoint:**
1. Define the request/response models in `schemas.py`. Only expose the fields the client needs.
2. Add the route to `users.py` / `jobs.py` (or a new router file, included in
   `api/__init__.py`). The router's `dependencies=[Depends(require_api_key)]` protects
   every route in it automatically.
3. Validate against `app/choices.py` instead of hard-coding lists.
4. Check it in `/api/v1/docs`, update this file, and tell the clients what's new.

## Known limits

- **API keys aren't company-scoped.** A key can see and change jobs for every company. If
  a client should only see some companies, that needs a `companies` column on
  `api_keys` and a filter in `jobs.py`.
- **There's no audit trail of which key changed a job's location.** `jobs.updated_at`
  records when it changed. If you need "who changed it", add an audit-log table.
- **The API can't delete users or jobs**, by design. Deactivate a user with
  `PATCH /users/{id}` and `{"is_active": false}`.
