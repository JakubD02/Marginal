# Marginal
![CI](https://github.com/JakubD02/marginal/actions/workflows/linting.yml/badge.svg)

A Python CLI for small business profitability analysis. Model your business as a scenario with products, costs, and traffic assumptions - then run monthly and annual P&L simulations with break-even analysis.

## Why this exists

Small business owners often make pricing and cost decisions without seeing the full financial picture. Marginal lets you model "what if" scenarios before committing capital: what if rent goes up? What if wastage drops from 8% to 5%? What if July traffic doubles due to seasonality?

Instead of building a spreadsheet from scratch, Marginal provides a domain-modeled system with unit economics, contribution margins, break-even point calculation, and monthly P&L across a full year.

## Features

- **Scenario management** - create, update, delete named business scenarios
- **Product & recipe modeling** - products with ingredient recipes, per-portion costs, wastage
- **Fixed costs** - categorized monthly costs (rent, utilities, insurance, etc.)
- **Traffic assumptions** - daily customers × products per customer
- **Seasonality factors** - monthly multipliers for realistic revenue projections
- **Full simulation** - contribution margin, BEP, monthly and annual P&L
- **Persistent storage** - SQLite with Alembic migrations
- **Interactive CLI** - Typer-based with `--help` for every command

## Quickstart

### Install

```bash
git clone https://github.com/JakubD02/marginal.git
cd marginal
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### Initialize database

```bash
alembic upgrade head
```

### Load example scenario

```bash
seed
```

Or with the full module path:

```bash
python -m marginal.scripts.seed
```

This creates an ice cream parlor scenario with 8 ingredients, seasonal traffic (2.5x in July), and 5000 PLN monthly fixed costs.

## Run a simulation

```bash
marginal simulate "Ice cream parlor 59"
```

Or without the entry point:

```bash
python -m marginal.cli simulate "Ice cream parlor 59"
```

Output:
```
============================================================

Ice cream parlor 59 (PLN)

Fixed costs: 5000 PLN/month
Contribution margin: 8.21 per portion (91.2%)

Monthly P&L:
Month Portions Revenue Variable Profit
 1        366        2928         289        -2361 ✗
 2        366        2928         289        -2361 ✗
...
7 1830 14640 1447 8193 ✓
8 1683 13464 1331 7133 ✓
...

Annual 87840 8681 24159
```

## Commands

### Scenarios

```bash
marginal scenario list
marginal scenario show "Ice cream parlor 59"
marginal scenario create "Cafe Milano" --currency EUR --working-days 24
marginal scenario update "Cafe Milano" --working-days 26
marginal scenario delete "Cafe Milano" --force
```

### Products

```bash
marginal product list "Ice cream parlor 59"
marginal product get "Ice cream parlor 59" "Strawberry ice cream scoop"
marginal product create "Cafe Milano" "Espresso" --price 8 --category food --wastage 0.03
marginal product update "Cafe Milano" "Espresso" --price 9
marginal product delete "Cafe Milano" "Espresso"
```

### Fixed costs

```bash
marginal fixed-cost list "Ice cream parlor 59"
marginal fixed-cost add "Ice cream parlor 59" "Insurance" 200 --category insurance
marginal fixed-cost delete "Ice cream parlor 59" "Insurance"
```

### Traffic & seasonality

```bash
marginal traffic-assumption set "Ice cream parlor 59" --customers 150 --avg-product 2.5
marginal traffic-assumption get "Ice cream parlor 59"

marginal seasonality set "Ice cream parlor 59" --month 7 --multiplier 2.5
marginal seasonality list "Ice cream parlor 59"
```

### Full simulation

```bash
marginal simulate "Ice cream parlor 59"
```

## Architecture

Marginal follows a layered architecture, with all code organized under the `marginal/` package:

- **`marginal/models.py`** — SQLAlchemy 2.0 domain entities (Scenario, Product, Ingredient, RecipeItem, FixedCost, TrafficAssumption, SeasonalityFactor)
- **`marginal/repository.py`** — data access layer with eager loading via `selectinload`
- **`marginal/calculations.py`** — pure functions for unit cost, contribution margin, BEP, monthly P&L
- **`marginal/presenters.py`** — display formatting (plain print, Rich planned)
- **`marginal/cli.py`** — Typer-based CLI with sub-apps for each entity
- **`marginal/schemas.py`** — Pydantic v2 schemas for validation
- **`marginal/scripts/`** — utility scripts (seed data, smoke tests)
- **`alembic/`** — database migrations

Financial calculations use `Decimal` throughout to avoid float precision errors.

## Tech stack

- Python 3.13
- SQLAlchemy 2.0 (ORM with typed mappers)
- Pydantic v2 (validation)
- Typer (CLI framework)
- SQLite (persistence)
- Alembic (migrations)
- Ruff (linting and formatting)
- GitHub Actions (CI/CD)

## Roadmap

### v0.1 (current)

- Domain model with 7 entities
- Repository pattern with eager loading
- Contribution margin, BEP, monthly P&L calculations
- Full CLI CRUD for all entities
- Deterministic simulation output

### v0.2 (next)

- pytest test suite for calculations and repository layer
- GitHub Actions CI (test + lint on every push)
- Export commands (`marginal export --format json/csv/html`)


### v0.3 — realistic sales modeling (planning)

Currently the simulator assumes all products sell in equal proportion — a naive arithmetic average. Real businesses have uneven demand: 60% of ice cream customers may buy vanilla, only 10% pick premium flavors. This distorts BEP calculations by 10-20% in practice.

- **`expected_sales_share` field on Product** — each product declares its % of total scenario sales (must sum to 1.0)
- **Weighted contribution margin** — replaces arithmetic mean with sales-share-weighted average
- **Per-product BEP breakdown** — shows exactly how many units of each product must sell to break even, not just a total
- **Validation** — sales shares are enforced to sum to 1.0 per scenario, with clear error messages


### v0.4 — tax and pricing realism

Financial simulations currently show gross figures — no tax handling. For Polish (and most EU) small businesses, VAT is a first-class concern that affects pricing decisions and cashflow.

- **VAT rates per product** — configurable VAT rate (0%, 5%, 8%, 23% in Poland) with default per scenario
- **Net vs gross price separation** — `price_gross` shown to customer, `price_net` used for margin calculation
- **VAT liability in P&L** — monthly VAT owed to tax authority separated from net profit

### v0.5 — AI-powered advisor

Once the simulation model is complete, adding an LLM as an analysis layer becomes powerful. The simulator produces structured business data; Claude interprets it and suggests optimizations.

- **`marginal advise <scenario>` command** — sends full scenario context to Anthropic API, returns 3-5 actionable recommendations
- **Streaming output** — recommendations appear progressively via Rich
- **Contextual suggestions** — "your wastage of 8% is high for gastro industry; reducing to 5% would save ~2400 PLN annually"
- **What-if exploration** — `marginal advise --what-if "price up 10%"` runs a simulation variant and explains impact
- **Tool use** — Claude can invoke calculations directly, e.g. re-run simulation with modified parameters mid-conversation

### Long-term vision

Marginal aims to become the tool a small business owner opens **before** signing a lease or launching a product — the same way developers open a REPL before writing production code. Fast iteration on financial models, with realistic assumptions and AI-assisted interpretation, replacing the "gut feeling + Excel spreadsheet" approach that currently dominates small business planning.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check .
ruff format .

# Run tests (coming in v0.2)
pytest
```
