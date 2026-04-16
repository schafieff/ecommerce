# `database.py` Mental Model (Beginner-Friendly)

This file explains how `app/database.py` works as a system, not just line by line.

---

## 1) The Core Idea

Your app needs a safe, repeatable way to:

1. connect to PostgreSQL,
2. run database operations per request,
3. save changes when successful,
4. undo changes when something fails.

`database.py` is that safety layer.

Think of it like this:

- **Engine** = road + transport system to database
- **Session** = one work notebook for one request
- **Transaction** = all-or-nothing operation scope
- **Commit** = finalize notebook into permanent record
- **Rollback** = throw away broken notebook changes

---

## 2) How Each Part Depends on the Others

## A. Engine

```python
engine = create_async_engine(settings.DATABASE_URL, echo=True)
```

- The engine knows *where* the DB is and manages connections.
- `echo=True` prints SQL statements for debugging.

Why others need it:
- Session factory cannot create sessions without an engine.

If missing:
- No DB communication at all.

---

## B. Session Factory (`AsyncSessionLocal`)

```python
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

- This is a **factory**. Each call to `AsyncSessionLocal()` gives a fresh session.
- Session = your "unit of work" for one request.

Why others need it:
- `get_db()` uses it to create per-request sessions.

If missing:
- Every route must manually create sessions (easy to forget cleanup/rollback).

Why `expire_on_commit=False` matters:
- After commit, objects keep loaded data available.
- Easier for beginners; avoids confusing "object expired" behavior.

---

## C. Declarative Base (`Base`)

```python
Base = declarative_base()
```

- Parent class for ORM models (`User`, `Product`, etc.).
- Holds metadata about all mapped tables.

Why others need it:
- Models inherit from `Base` so SQLAlchemy understands table mapping.

If missing:
- ORM models become inconsistent or impossible in standard pattern.

---

## D. Dependency Function (`get_db`)

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- Creates one session for one request.
- Yields it to route/service code.
- Commits on success.
- Rolls back on any exception.
- Re-raises exception so API returns an error correctly.

Why others need it:
- This is where transaction lifecycle is enforced.

If missing:
- You lose centralized safety; bugs from inconsistent DB handling increase.

---

## 3) Request Lifecycle (Direct Steps)

When a route depends on `get_db`:

1. FastAPI enters `get_db`.
2. A session is created (`AsyncSessionLocal()`).
3. Session is handed to route via `yield session`.
4. Route/service performs DB reads/writes.
5. If route finishes without exception -> `commit()`.
6. If any exception happens -> `rollback()`.
7. Function exits; `async with` closes session automatically.

This ensures each request gets isolated DB work with cleanup.

---

## 4) Commit vs Rollback (What Actually Happens)

## Commit

- Makes transaction changes permanent in PostgreSQL.
- Example: create order + reduce stock + write payment row -> all saved.

Without commit:
- Changes may not persist (not finalized transaction).

## Rollback

- Cancels uncommitted changes in current transaction.
- Example: order insert succeeded, stock update failed -> rollback removes order insert too.

Without rollback:
- You risk partial, inconsistent business data.

---

## 5) Critical "What If We Remove This?" Cases

## If we do not initialize session factory

- No standard way to create request sessions.
- Developers may open raw sessions inconsistently.
- Higher chance of connection leaks and missing rollback.

## If we do not use `async with ... as session`

- Session may not close properly on errors.
- Connection pool can be exhausted over time.

## If we do not `commit()`

- Writes are not finalized.
- App might appear to work in memory but DB is unchanged.

## If we do not `rollback()` in `except`

- Failed transaction leaves dirty state for that session.
- In more complex flows, this can cascade into later failures.

## If we remove `raise` after rollback

- Error is swallowed.
- API might return success even though DB work failed.

---

## 6) Why This Pattern Is Good for Beginners

- One place controls DB session lifecycle.
- One place handles transaction success/failure.
- Route code stays focused on business logic.
- Easy to reason about: "success = commit, failure = rollback."

---

## 7) Tiny Example Flow

Imagine `POST /orders`:

1. `get_db` gives session.
2. Route adds new `Order`.
3. Route updates inventory.
4. Inventory update fails (negative stock).
5. Exception raised.
6. `get_db` catches exception -> rollback.
7. No order remains in DB (all-or-nothing preserved).

That is exactly why commit/rollback exists together.
