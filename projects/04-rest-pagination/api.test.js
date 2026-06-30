const test = require("node:test");
const assert = require("node:assert");
const { listUsers } = require("./api");

test("first page with explicit limit", () => {
  const r = listUsers({ page: 1, limit: 10 });
  assert.equal(r.data.length, 10);
  assert.equal(r.data[0].id, 1);
  assert.equal(r.data[9].id, 10);
  assert.equal(r.total, 25);
  assert.equal(r.totalPages, 3);
});

test("second page", () => {
  const r = listUsers({ page: 2, limit: 10 });
  assert.equal(r.data.length, 10);
  assert.equal(r.data[0].id, 11);
});

test("last page is partial", () => {
  const r = listUsers({ page: 3, limit: 10 });
  assert.equal(r.data.length, 5);
  assert.equal(r.data[0].id, 21);
  assert.equal(r.data[4].id, 25);
});

test("defaults to page 1, limit 10", () => {
  const r = listUsers();
  assert.equal(r.page, 1);
  assert.equal(r.limit, 10);
  assert.equal(r.data.length, 10);
});
