// In-memory "database" of 25 users (ids 1..25).
const USERS = Array.from({ length: 25 }, (_, i) => ({
  id: i + 1,
  name: `user${i + 1}`,
}));

/**
 * List users.
 *
 * Currently returns every user and ignores any pagination parameters.
 *
 * @param {{ page?: number, limit?: number }} [query]
 * @returns {{ data: Array, page: number, limit: number, total: number, totalPages: number }}
 */
function listUsers(query = {}) {
  return {
    data: USERS,
    page: 1,
    limit: USERS.length,
    total: USERS.length,
    totalPages: 1,
  };
}

module.exports = { listUsers, USERS };
