ALTER TABLE books ADD COLUMN category TEXT;

-- Books that are fiction AND have more than 2 copies
SELECT * FROM books
WHERE category = 'Fiction' AND total_copies > 2;

-- Members who joined in 2024 OR 2025
SELECT * FROM members
WHERE joined_date >= '2024-01-01' AND joined_date < '2026-01-01';

-- Mixing AND/OR — parentheses matter
SELECT * FROM books
WHERE category = 'Fiction' AND (total_copies > 5 OR author = 'Toni Morrison');


-- Instead of: category = 'Fiction' OR category = 'Sci-Fi' OR category = 'Fantasy'
SELECT * FROM books
WHERE category IN ('Fiction', 'Sci-Fi', 'Fantasy');

SELECT * FROM borrows
WHERE borrow_date BETWEEN '2026-01-01' AND '2026-01-31';

SELECT * FROM borrows
WHERE borrow_date BETWEEN '2026-01-01' AND '2026-01-31';

-- Titles starting with "The"
SELECT * FROM books WHERE title LIKE 'The%';

-- Authors with "Martin" anywhere in the name
SELECT * FROM books WHERE author LIKE '%Martin%';

-- Case-insensitive version (Postgres-specific)
SELECT * FROM books WHERE author ILIKE '%martin%';

-- How many books do we have in total?
SELECT COUNT(*) FROM books;

-- Total copies across the whole library
SELECT SUM(total_copies) FROM books;

-- Average copies per title
SELECT AVG(total_copies) FROM books;

-- Earliest and latest member join dates
SELECT MIN(joined_date), MAX(joined_date) FROM members;


-- Count of books per category
SELECT category, COUNT(*) AS num_books
FROM books
GROUP BY category;


-- Only categories with more than 10 books
SELECT category, COUNT(*) AS num_books
FROM books
GROUP BY category
HAVING COUNT(*) > 10;

-- WHERE filters rows first, HAVING filters the resulting groups
SELECT category, AVG(total_copies) AS avg_copies
FROM books
WHERE total_copies > 0        -- exclude out-of-print entries, row-level
GROUP BY category
HAVING AVG(total_copies) > 3; -- only categories averaging more than 3 copies, group-level

SELECT category, COUNT(*) AS num_books
FROM books
GROUP BY category
ORDER BY num_books DESC;

SELECT m.member_id, m.name, COUNT(b.borrow_id) AS total_borrows
FROM members m
LEFT JOIN borrows b ON m.member_id = b.member_id
GROUP BY m.member_id, m.name
ORDER BY total_borrows DESC;

-- Books currently borrowed (not yet returned)
SELECT * FROM borrows WHERE return_date IS NULL;

-- Books that have been returned
SELECT * FROM borrows WHERE return_date IS NOT NULL;

-- If any book_id in the subquery is NULL, this returns ZERO rows, unexpectedly
SELECT * FROM books WHERE book_id NOT IN (SELECT book_id FROM borrows);



SELECT * FROM books
WHERE book_id NOT IN (SELECT book_id FROM borrows WHERE book_id IS NOT NULL);

