-- Basic single-column index
CREATE INDEX idx_books_author ON books(author);

-- Composite index — useful when you frequently filter on both columns together
CREATE INDEX idx_borrows_member_date ON borrows(member_id, borrow_date);

-- Unique index — enforces uniqueness AND speeds up lookups
CREATE UNIQUE INDEX idx_members_email ON members(email);

EXPLAIN ANALYZE
SELECT * FROM books WHERE author = 'Robert Martin';

Seq Scan on books  (cost=0.00..1834.00 rows=12 width=64) (actual time=0.05..14.2 rows=12 loops=1)
  Filter: (author = 'Robert Martin'::text)
  Rows Removed by Filter: 49988
Planning Time: 0.1 ms
Execution Time: 14.3 ms


Index Scan using idx_books_author on books  (cost=0.29..8.45 rows=12 width=64) (actual time=0.02..0.04 rows=12 loops=1)
  Index Cond: (author = 'Robert Martin'::text)
Execution Time: 0.06 ms


CREATE INDEX idx_books_author ON books(author);
CREATE UNIQUE INDEX idx_members_email ON members(email);


