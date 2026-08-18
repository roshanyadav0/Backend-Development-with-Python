SELECT m.name, b.title, br.borrow_date
FROM members m
INNER JOIN borrows br ON m.member_id = br.member_id
INNER JOIN books b ON br.book_id = b.book_id;

SELECT m.name, br.borrow_date
FROM members m
RIGHT JOIN borrows br ON m.member_id = br.member_id;

SELECT m.name, br.borrow_date
FROM members m
FULL OUTER JOIN borrows br ON m.member_id = br.member_id;

SELECT
    m.member_id,
    m.name,
    b.title,
    br.borrow_date,
    br.return_date
FROM members m
LEFT JOIN borrows br ON m.member_id = br.member_id
LEFT JOIN books b ON br.book_id = b.book_id
ORDER BY m.name, br.borrow_date;

SELECT m.name, COUNT(br.borrow_id) AS total_borrows
FROM members m
LEFT JOIN borrows br ON m.member_id = br.member_id
GROUP BY m.member_id, m.name
ORDER BY total_borrows DESC;

