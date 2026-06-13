# M&A Target Intelligence Engine

A Python engine that screens public companies as M&A acquisition targets, scoring each against a defined acquirer thesis and stress-testing the ranking across different buyer profiles.

## The acquirer thesis

The screen is built around a specific strategic buyer: **a large enterprise-software incumbent seeking to acquire a growth asset to defend against AI-native disruption.** This buyer already has scale, profitability, and a strong balance sheet — what it lacks, and is buying, is growth and innovation momentum. That thesis drives the scoring weights: growth and quality of earnings are rewarded heavily, while cheap valuation and low leverage are de-emphasised, because they are not what this acquirer is short of.

## What the engine does

A six-step pipeline, fully reproducible end to end:

1. **Ingest** — pulls live financial fundamentals for a universe of public companies via the Yahoo Finance API.
2. **Clean** — coerces data types and handles missing values through median imputation, dealing with the messiness of real-world financial data.
3. **Score** — normalises five metrics (revenue growth, profitability, return on equity, valuation, leverage) to a common scale, applies thesis-driven weights, and produces a 0–100 target score.
4. **Tier** — buckets each company into Pursue / Monitor / Pass using a deliberately strict threshold, keeping the shortlist small and actionable.
5. **Stress-test** — re-scores every company under three different acquirer profiles (growth-defense, value-disciplined, balance-sheet-cautious) to separate thesis-robust targets from thesis-dependent ones.
6. **Deliver** — exports a multi-sheet Excel report and a growth-versus-valuation strategic visual.

The central insight the engine surfaces: the most attractive acquisition target depends on who is buying and why — with the top candidate holding its rank across every profile, making it a conviction call rather than an artefact of the assumptions.

## Tools used

- **Python** — core language
- **pandas** — data cleaning, transformation, and scoring logic
- **yfinance** — live financial data from the Yahoo Finance API
- **matplotlib** — the growth-versus-valuation strategic matrix
- **openpyxl** — multi-sheet Excel report export

## How to run

```bash
pip install -r requirements.txt
python ma_engine.py
```

The script prints the rankings, tiers, and sensitivity analysis to the console, and writes `ma_target_report.xlsx` and `ma_target_matrix.png` to the project folder.

## What I learned

I built this in three days as my final project for Stanford Code in Place, coming in with no prior programming background. Beyond the Python fundamentals, the real lesson was in translation: turning a strategic question into measurable criteria, handling data that rarely arrives clean, and being honest about what a model can and can't see. The hardest and most valuable part wasn't writing the code — it was deciding what the code should measure and being able to defend those choices.

---

*This is a learning project and a first-pass screening prototype. It is not investment advice and does not make acquisition recommendations on its own.*

