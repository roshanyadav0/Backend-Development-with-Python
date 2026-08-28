Same drill format as your prior week reviews — attempt everything cold, no scrolling back, before checking yourself.

## Rebuild all PyMongo exercises from scratch

Close every previous MongoDB day's code. Working only from memory, write:

1. A `MongoClient` connection, and a reference to a `library_docs` database and a `borrow_log` collection.
2. One `insert_one()` call creating a borrow event with an embedded `member` and `book` sub-document.
3. One `insert_many()` call inserting three more events.
4. A `find()` call with a comparison operator (`$gt` or `$lt`) on a date field.
5. A `find()` call using `$in` across a list of category values.
6. A `find_one()` call by a nested field using dot notation (`"member.member_id"`).
7. An `update_one()` call that correctly uses `$set` — and explain out loud what would happen to the document if you forgot `$set`.
8. A `delete_one()` call.
9. A `find()` chained with `.sort()` and `.limit()`.

Before checking anything, go through #7 specifically and actually say out loud what breaks without `$set`. If you can't state it precisely — "the whole document gets replaced with just this one field, silently deleting everything else" — that's the one gap from this whole month worth closing before moving on, since it's a live data-loss bug, not a stylistic preference.

## Write 3 aggregation pipelines without docs

No `read_me`, no scrolling to Day 21 — write these as raw pipeline arrays from memory:

1. Count how many borrow events exist per `book.category`, sorted highest first.
2. Find every member whose total borrow count exceeds 5 — meaning your pipeline needs `$group` followed by a *second* `$match` acting as `HAVING`, not the first `$match`.
3. Find the single most-recently-active member — the member with the most recent `timestamp` across all their borrow events (hint: this needs `$sort` *before* `$group`, using `$first` inside `$group` to capture the top document per group after that sort — the opposite ordering from #1 and #2, and worth noticing why).

That third one is deliberately the hardest of the three, because it inverts the "sort after group" instinct #1 and #2 both reinforce. If you got it wrong, the lesson isn't "always sort after group" — it's "the right stage order depends on what you're actually trying to preserve going into the group," which is a sharper, truer rule than any fixed ordering habit.

## Compare: when would you use MongoDB over Postgres for a new project?

Write your own answer before reading further — a few sentences, in your own words, not just "it depends."

The honest comparison, building on Day 18's framing:

**Reach for MongoDB when:**
- Your data's natural unit is read and written together as one shape, and that shape genuinely varies between records (a product catalog spanning categories with different attributes; user-generated content with optional, evolving fields)
- You're building something append-only and high-volume where individual records rarely need cross-record consistency — event logs, analytics, activity feeds, sensor readings
- Your schema is going to change frequently and unpredictably early on, and you don't want a migration (Day 12/13's discipline) gating every iteration
- You need horizontal scale across many machines more than you need strict cross-entity guarantees — document databases were built with sharding as a first-class concern in a way Postgres wasn't originally designed around

**Reach for Postgres when:**
- Multiple entities need to stay consistent with each other under concurrent writes — money, inventory counts, anything where Day 7's ACID transactions and Day 15's row-level locking are load-bearing, not optional
- Your data's relationships are genuinely many-to-many and queried from multiple angles — a library's books/members/borrows is the textbook case, since you regularly need "everything this member borrowed" *and* "everyone who's borrowed this book," and normalized tables with real joins serve both directions equally well
- You want the database itself to catch bad data — `NOT NULL`, `CHECK`, `UNIQUE`, foreign keys enforcing correctness even when application code has a bug (Day 17's defense-in-depth argument)
- Your team's actual pattern is ad hoc analytical queries against relationships nobody predicted in advance — SQL's declarative `JOIN` handles "give me an answer to a question I didn't design the schema for" far better than a document model optimized around specific known access patterns

**The honest middle ground**, which is where most real systems actually land: many production systems use both, for different parts of the same product — exactly like your own 22 days here. The Library API's core transactional data (`books`, `members`, `borrows`) stays in Postgres because it needs real consistency guarantees. A `borrow_log` collection for analytics and activity history lives in MongoDB because it's append-only, read in bulk, and doesn't need to join against anything. Picking "the database" for a whole project is often the wrong question — the better one is "what does *this specific data* need," asked separately for each part of the system.

## Design your borrow log document schema on paper

Before checking against anything below, draw this from scratch: what fields does a single `borrow_log` document need, and why each one is shaped the way it is.

Your design should show deliberate reasoning about three decisions specifically:

1. **What's embedded vs what's just an ID.** You embedded `member.name` and `member.email` back in Day 19 — was that the right call for *every* field, or would `member.member_id` alone plus a manual lookup have been better for some fields? (There's a real trade-off here: embedding more makes this document more self-sufficient to query, but makes it more stale if the source data changes, and larger to store per event.)
2. **What's queried directly vs what's just carried along for display.** `member.member_id` and `timestamp` get queried constantly (Day 20's 30-day challenge, Day 21's per-member aggregation) — those need to be structured for indexing and comparison. `book.author`, by contrast, might just be display data nobody filters on.
3. **What changes after the document is created, and what's immutable.** `returned` and `return_timestamp` are the only fields this document expects to `$set` later (Day 19's update pattern). Everything else — `member`, `book`, `borrow_date`, `due_date` — should be treated as write-once, a snapshot of what was true when the event happened, never mutated afterward. If your paper design has you planning to update `member.email` on this document later, that's worth catching now: it signals you're treating this log as a live reference rather than a historical record, which contradicts the entire reason it's denormalized in the first place.

A reasonable version to check your own against:

```javascript
{
  _id: ObjectId("..."),
  event: "borrow",                    // immutable — what happened
  timestamp: ISODate("..."),          // immutable, indexed — when it happened
  member: {                           // immutable snapshot
    member_id: 7,                     // indexed — the field you actually query on
    name: "Asha Rao",                 // display only
    email: "asha@mail.com"            // display only, arguably omit — rarely needed in a log
  },
  book: {                             // immutable snapshot
    book_id: 3,                       // indexed — queried
    title: "Clean Code",              // display
    author: "Robert Martin",          // display only
    category: "Programming"           // queried (Day 21's per-category counts)
  },
  due_date: ISODate("..."),           // immutable
  returned: false,                    // mutable — the one field this doc expects to update
  return_timestamp: null              // mutable, set alongside `returned`
}
```

If your version dropped `member.email` from the log or questioned whether it belongs there at all, that's good instinct, not a mistake to fix — it's genuinely borderline whether an activity log needs a contact field it will basically never query or display in that context, versus just carrying the `member_id` and `name` for identification. The right answer depends on whether anything downstream actually reads `member.email` off this specific collection — worth asking that question explicitly rather than embedding every field reflexively just because Day 19's example did.

---

If any of these four sections surfaced a real gap rather than a phrasing difference, that's exactly the value of a review day — better caught now than three days into building something on top of a shaky mental model.

Where would you like Day 23 to go — schema design patterns in more depth (the "one big document" anti-pattern, document size limits, when embedding becomes genuinely wrong), or wiring MongoDB into a real Python app with Motor or FastAPI, mirroring what Days 8-15 did for the Postgres side?