---
image: "/images/posts/2026-02-24-alembic-database-migration/cover.jpg"
title: "Alembic — Database Migration with SQLAlchemy"
description: "A practical guide to Alembic for version-controlled database schema migrations with SQLAlchemy — covering setup, the basic workflow, rollbacks, and useful features like post-write hooks and pyproject.toml support."
date: 2026-02-24
categories: ["backend"]
tags: ["alembic", "sqlalchemy", "database", "migration", "python", "postgresql"]
toc: true
math: false
---

## Overview

Database schemas change constantly as projects evolve — adding tables, modifying columns, creating indexes. Managing this manually makes it impossible to answer questions like "what changes have been applied to this database?" [Alembic](https://alembic.sqlalchemy.org/) is a migration tool for SQLAlchemy that lets you **version-control schema changes like code** and safely apply or roll them back.

<!--more-->

```mermaid
graph LR
    A[Model change] --> B[alembic revision]
    B --> C[Migration script generated]
    C --> D[alembic upgrade]
    D --> E[Schema applied to DB]
    E --> F{Problem?}
    F -->|Yes| G[alembic downgrade]
    F -->|No| H[Done]
    G --> A
```

## Migration Environment Structure

Running `alembic init` creates the following directory structure:

```
yourproject/
    alembic.ini          # Main config file (DB URL, logging, etc.)
    pyproject.toml       # Python project config
    alembic/
        env.py           # Migration runtime (DB connection, transaction management)
        README
        script.py.mako   # Template for generating migration scripts
        versions/        # Actual migration scripts
            3512b954651e_add_account.py
            2b1ae634e5cd_add_order_id.py
            3adcc9a56557_rename_username_field.py
```

### Role of Each Key File

**`alembic.ini`**: Global config — DB URL, logging, script paths. The `%(here)s` token lets you specify paths relative to the config file location.

**`env.py`**: The "brain" of migrations. Controls SQLAlchemy engine creation, DB connection, transaction management, and model imports. Modify this file when you need multi-DB support or custom arguments.

**`script.py.mako`**: A Mako template that defines the skeleton for new migration files. Customize the structure of the `upgrade()` and `downgrade()` functions here.

**`versions/`**: Where the actual migration scripts live. File names use **partial GUIDs** instead of integer sequences, enabling merges across branches.

## Basic Workflow

### Step 1: Initialize the Environment

```bash
cd /path/to/yourproject
alembic init alembic
```

Four templates to choose from:

| Template | Use Case |
|--------|------|
| `generic` | Single DB, basic setup |
| `pyproject` | pyproject.toml-based config (v1.16+) |
| `async` | Async DB drivers (asyncpg, etc.) |
| `multidb` | Multi-database environments |

### Step 2: Configure the DB Connection

Set the database URL in `alembic.ini`:

```ini
sqlalchemy.url = postgresql://user:pass@localhost/dbname
```

> **Note**: If the URL contains `%` characters (e.g., URL-encoded passwords), escape them as `%%`. Example: `p%40ss` → `p%%40ss`

### Step 3: Generate a Migration Script

```bash
alembic revision -m "add account table"
```

This creates a new migration file in `versions/`:

```python
"""add account table

Revision ID: 3512b954651e
Revises: 2b1ae634e5cd
Create Date: 2026-02-24 12:00:00.000000

"""

def upgrade():
    # Write schema change code here
    pass

def downgrade():
    # Write rollback code here
    pass
```

### Step 4: Apply the Migration

```bash
alembic upgrade head      # Upgrade to latest version
alembic upgrade +2        # Advance 2 steps from current position
```

### Step 5: Roll Back

```bash
alembic downgrade -1      # Roll back 1 step
alembic downgrade base    # Roll back all migrations
```

### Step 6: Check Status

```bash
alembic current           # Show current DB version
alembic history           # Show full migration history
alembic history -r1a:3b   # Show history for a specific range
```

## Useful Features

### Partial Revision IDs

You don't need to type the full Revision ID in commands — just enough characters to guarantee uniqueness:

```bash
alembic upgrade ae1027a6acf   # Full ID
alembic upgrade ae1            # This works too (if unique)
```

### Post-write Hooks

Automatically run a code formatter after generating a migration file:

```ini
[post_write_hooks]
hooks = ruff
ruff.type = module
ruff.module = ruff
ruff.options = check --fix REVISION_SCRIPT_FILENAME
```

Connect `black`, `ruff`, or similar tools to auto-format generated migration scripts.

### pyproject.toml Support

Since Alembic 1.16, you can manage configuration directly in `pyproject.toml`:

```bash
alembic init --template pyproject ./alembic
```

With this setup, source code settings go in `pyproject.toml` and environment-specific settings like DB connections stay in `alembic.ini`.

## Quick Links

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) — Official tutorial
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) — Real-world recipes
- [SQLAlchemy](https://www.sqlalchemy.org/) — The ORM that Alembic is built on

## Insights

Alembic's core value is treating DB schema changes like code. Just as `git log` lets you trace code change history, `alembic history` lets you trace schema change history. In team development, when someone asks "when was this table added?" or "who changed this column?", the migration scripts have the answer. Adopting Alembic early in a project prevents a large accumulation of untracked schema debt later. The GUID-based versioning design — rather than integer sequences — is also worth noting: it enables merges across multiple branches where migrations are created concurrently.
