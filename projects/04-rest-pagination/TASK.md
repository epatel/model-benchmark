# Task: Add pagination to `listUsers`

`api.js` exposes `listUsers(query)` which currently returns **all** users and
ignores pagination. Add real pagination driven by `query.page` and
`query.limit`.

Requirements:

- `page` is **1-indexed**; default `1`. `limit` default `10`.
- Return an object: `{ data, page, limit, total, totalPages }`.
  - `data` is the slice of users for the requested page.
  - `total` is the total number of users (not the page size).
  - `totalPages = ceil(total / limit)`.
- The **last page** may be partial (e.g. 25 users, limit 10 → page 3 has 5).
- A page **beyond the last** returns an empty `data` array (not an error).
- Treat `page`/`limit` passed as numeric strings (e.g. `"2"`) the same as numbers.

Do not change the export shape (`module.exports = { listUsers, USERS }`).

Run `node --test` in this directory to check your work.
