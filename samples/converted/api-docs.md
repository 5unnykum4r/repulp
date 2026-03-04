# Acme API Documentation

Version 3.0 | Base URL: `https://api.acme.io/v3`

The Acme API provides programmatic access to manage users, projects,
and billing. All requests require an API key passed via the
`Authorization: Bearer <token>` header.

## Authentication

Generate API keys from your [account settings](https://app.acme.io/settings/api).
Keys are scoped to either **read-only** or **read-write**.
Rate limit: 1000 requests/minute for standard plans, 10,000 for enterprise.

## Endpoints

### Users

| Method | Path          | Description                        | Auth  |
| ------ | ------------- | ---------------------------------- | ----- |
| GET    | `/users`      | List all users in the organization | read  |
| GET    | `/users/{id}` | Get a single user by ID            | read  |
| POST   | `/users`      | Create a new user                  | write |
| PATCH  | `/users/{id}` | Update user fields                 | write |
| DELETE | `/users/{id}` | Deactivate a user (soft delete)    | write |

### Projects

| Method | Path                     | Description               | Auth  |
| ------ | ------------------------ | ------------------------- | ----- |
| GET    | `/projects`              | List all projects         | read  |
| POST   | `/projects`              | Create a new project      | write |
| GET    | `/projects/{id}/members` | List project members      | read  |
| POST   | `/projects/{id}/members` | Add a member to a project | write |

### Billing

| Method | Path                     | Description                  | Auth  |
| ------ | ------------------------ | ---------------------------- | ----- |
| GET    | `/billing/invoices`      | List all invoices            | read  |
| GET    | `/billing/invoices/{id}` | Download invoice PDF         | read  |
| GET    | `/billing/usage`         | Current billing period usage | read  |
| PUT    | `/billing/plan`          | Change subscription plan     | write |

## Error Codes

| Code | Meaning               | Resolution                                        |
| ---- | --------------------- | ------------------------------------------------- |
| 400  | Bad Request           | Check request body against the schema             |
| 401  | Unauthorized          | Verify your API key is valid and not expired      |
| 403  | Forbidden             | Your key lacks the required scope (read vs write) |
| 404  | Not Found             | The resource ID does not exist                    |
| 429  | Rate Limited          | Wait for the duration in the Retry-After header   |
| 500  | Internal Server Error | Contact support@acme.io with your request ID      |

## Webhooks

Configure webhooks at [webhook settings](https://app.acme.io/settings/webhooks).
Events are delivered with HMAC-SHA256 signatures in the `X-Acme-Signature` header.

Supported events:

* `user.created` — Fired when a new user is added
* `user.deleted` — Fired when a user is deactivated
* `project.created` — Fired when a new project is created
* `invoice.paid` — Fired when an invoice payment succeeds
* `invoice.failed` — Fired when a payment attempt fails

## SDKs

Official client libraries:

* [Python](https://github.com/acme/acme-python) — `pip install acme-sdk`
* [Node.js](https://github.com/acme/acme-node) — `npm install @acme/sdk`
* [Go](https://github.com/acme/acme-go) — `go get github.com/acme/acme-go`
* [Ruby](https://github.com/acme/acme-ruby) — `gem install acme-sdk`

## Changelog

| Version | Date       | Changes                                                    |
| ------- | ---------- | ---------------------------------------------------------- |
| 3.0     | 2025-11-01 | Added billing endpoints, webhook signatures, rate limiting |
| 2.1     | 2025-06-15 | Added project members endpoints, pagination support        |
| 2.0     | 2025-01-10 | Breaking: new auth model, removed legacy XML responses     |
| 1.0     | 2024-03-01 | Initial release with users and projects                    |