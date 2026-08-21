BEGIN;

UPDATE books SET available_copies = available_copies - 1 WHERE book_id = 3;
INSERT INTO borrows (member_id, book_id, borrow_date, due_date)
VALUES (7, 3, CURRENT_DATE, CURRENT_DATE + 14);

COMMIT;



BEGIN;

UPDATE books SET available_copies = available_copies - 1 WHERE book_id = 3;
-- something's wrong, changed your mind, or an error occurred
ROLLBACK;

-- available_copies is back to its original value, as if nothing happened


-- No transaction: these are two independent, uncoordinated operations
UPDATE books SET available_copies = available_copies - 1 WHERE book_id = 3;
INSERT INTO borrows (member_id, book_id, borrow_date, due_date) VALUES (7, 3, CURRENT_DATE, CURRENT_DATE + 14);



BEGIN;
SELECT available_copies FROM books WHERE book_id = 3; -- say this returns 1
-- meanwhile, someone else's transaction commits a borrow, dropping it to 0
SELECT available_copies FROM books WHERE book_id = 3; -- could now return 0
COMMIT;


BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- ... your borrow logic ...
COMMIT;



-- Step 1: check the starting state
SELECT available_copies FROM books WHERE book_id = 3;

-- Step 2: start a transaction and make a change
BEGIN;
UPDATE books SET available_copies = available_copies - 1 WHERE book_id = 3;

-- Step 3: check it — from the SAME session, you'll see the new value
SELECT available_copies FROM books WHERE book_id = 3;

-- Step 4: open a SECOND psql window/session and run the same SELECT there.
-- It will still show the ORIGINAL value — your uncommitted change is invisible
-- to other sessions. This is isolation in action.

-- Step 5: back in the first session, force a failure deliberately
INSERT INTO borrows (member_id, book_id, borrow_date, due_date)
VALUES (999, 3, CURRENT_DATE, CURRENT_DATE + 14);
-- if member_id 999 doesn't exist, the FK constraint rejects this insert

-- Step 6: since the transaction failed partway, undo everything
ROLLBACK;

-- Step 7: confirm available_copies is back to its original value
SELECT available_copies FROM books WHERE book_id = 3;



