This is exactly the right instinct — a no-notes drill is what actually converts "I read about it" into "I can do it." I'll give you the 15 challenges as plain-English prompts (writing the SQL is on you), then a schema recall exercise, then a self-audit checklist, with the answer key folded in at the very bottom so you're not tempted to peek early.

**Schema reminder** (no columns shown — that's part of the test, you should already know these by heart):
`books`, `members`, `borrows`

## The 15 challenges

Write these from scratch. No looking back at earlier days.

1. List all books in the `'Fiction'` category, ordered alphabetically by title.
2. Find all members who joined between `2023-01-01` and `2024-12-31`.
3. Find all books whose title starts with "The" **or** whose title contains "Guide".
4. Find all books in the categories `'Fiction'`, `'Sci-Fi'`, or `'Fantasy'` that have more than 3 copies.
5. Count how many books exist in each category.
6. Find only the categories that have more than 10 books.
7. Find the average number of copies per category — but only show categories averaging more than 2 copies.
8. List every member's name with the total number of books they've borrowed. Members who've never borrowed anything should show `0`, not disappear.
9. List every book's title with how many times it's been borrowed. Books never borrowed should show `0`.
10. Find all borrow records that are still active (not yet returned).
11. Find all members who have never borrowed a single book.
12. Find the 5 most-borrowed books, most borrows first.
13. Find the single member who has borrowed the most books overall.
14. List the 10 most recent borrow records, showing the member's name and the book's title (not just their IDs).
15. **Harder**: find every book that's currently fully checked out — meaning its `total_copies` equals the number of currently active (unreturned) borrows for that book.

Don't rush #15. It requires combining a `JOIN`, a `GROUP BY`, and a `HAVING` that compares an aggregate to a column from the other table — that's a real synthesis of the whole week.

## Schema recall — draw it, then explain out loud

On paper, redraw `books`, `members`, `borrows` from memory — no peeking at Day 1. For each table, write out:

- Every column, and mark which one is the PK
- Every FK, and which table/column it points to

Then explain, in your own words, out loud or in writing, each of these:

- Why is `borrows` its own table instead of just adding a `member_id` column directly onto `books`?
- What kind of relationship exists between `members` and `borrows`? Between `books` and `borrows`?
- What kind of relationship does `borrows` effectively create *between* `members` and `books`, indirectly?
- Why is `return_date` nullable, and what does that `NULL` mean in a query?

If you can't explain the third bullet clearly, that's the one gap worth closing before Day 6 — it's the concept that everything else (JOINs, aggregates) sits on top of.

## Common gaps — self-audit before moving on

Go through your 15 answers and check for these specific mistakes, since they're the ones that silently produce wrong-but-plausible-looking results:

- Did you use `INNER JOIN` anywhere it should've been `LEFT JOIN` — causing zero-count members or never-borrowed books to vanish instead of showing `0`?
- In any `GROUP BY` query, is every non-aggregated `SELECT` column also in the `GROUP BY` clause?
- Did you use `HAVING` to filter on an aggregate (like `COUNT(*) > 10`) rather than mistakenly trying to put that in `WHERE`?
- Anywhere you checked for "no borrows" or "no return date," did you use `IS NULL` rather than `= NULL`?
- In #8 and #9, did you count the right column (`COUNT(br.borrow_id)`, not `COUNT(*)`) so that a `LEFT JOIN`'s `NULL`-padded row correctly counts as `0` rather than `1`?
- Any ambiguous column error? Once you `JOIN` two tables that both have `member_id` or similar, you need `table.column` or an alias everywhere that column is referenced.

If you hit any of these, that's a real gap — fix it now rather than carrying it into SQLAlchemy, where the ORM will hide the raw SQL and make the same mistake much harder to spot.

---

## Answer key
*(attempt all 15 first — this is only useful as a check, not a shortcut)*

1. `SELECT * FROM books WHERE category = 'Fiction' ORDER BY title;`
2. `SELECT * FROM members WHERE joined_date BETWEEN '2023-01-01' AND '2024-12-31';`
3. `SELECT * FROM books WHERE title LIKE 'The%' OR title LIKE '%Guide%';`
4. `SELECT * FROM books WHERE category IN ('Fiction','Sci-Fi','Fantasy') AND total_copies > 3;`
5. `SELECT category, COUNT(*) FROM books GROUP BY category;`
6. `SELECT category, COUNT(*) FROM books GROUP BY category HAVING COUNT(*) > 10;`
7. `SELECT category, AVG(total_copies) FROM books GROUP BY category HAVING AVG(total_copies) > 2;`
8. `SELECT m.name, COUNT(br.borrow_id) FROM members m LEFT JOIN borrows br ON m.member_id = br.member_id GROUP BY m.member_id, m.name;`
9. `SELECT b.title, COUNT(br.borrow_id) FROM books b LEFT JOIN borrows br ON b.book_id = br.book_id GROUP BY b.book_id, b.title;`
10. `SELECT * FROM borrows WHERE return_date IS NULL;`
11. `SELECT m.* FROM members m LEFT JOIN borrows br ON m.member_id = br.member_id WHERE br.borrow_id IS NULL;`
12. `SELECT b.title, COUNT(*) AS times_borrowed FROM books b JOIN borrows br ON b.book_id = br.book_id GROUP BY b.book_id, b.title ORDER BY times_borrowed DESC LIMIT 5;`
13. `SELECT m.name, COUNT(*) AS total FROM members m JOIN borrows br ON m.member_id = br.member_id GROUP BY m.member_id, m.name ORDER BY total DESC LIMIT 1;`
14. `SELECT m.name, b.title, br.borrow_date FROM borrows br JOIN members m ON br.member_id = m.member_id JOIN books b ON br.book_id = b.book_id ORDER BY br.borrow_date DESC LIMIT 10;`
15. `SELECT b.title FROM books b JOIN borrows br ON b.book_id = br.book_id AND br.return_date IS NULL GROUP BY b.book_id, b.title, b.total_copies HAVING COUNT(br.borrow_id) = b.total_copies;`

---

Once you've reconciled your answers, you're genuinely ready for Week 2. Want Day 6 lined up — typically the jump into SQLAlchemy would start with connecting to your `library` database, defining the three tables as ORM models, and running your first `session.query()` equivalents of a few queries from today's drill?