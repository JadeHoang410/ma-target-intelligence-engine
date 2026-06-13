# -*- coding: utf-8 -*-

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def get_company_data(ticker_symbol):
    """Pull key financial metrics for one company."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    data = {
        "Ticker": ticker_symbol,
        "Name": info.get("longName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Market_Cap": info.get("marketCap", None),
        "PE_Ratio": info.get("trailingPE", None),
        "Profit_Margin": info.get("profitMargins", None),
        "Revenue_Growth": info.get("revenueGrowth", None),
        "Debt_to_Equity": info.get("debtToEquity", None),
        "Free_Cash_Flow": info.get("freeCashflow", None),
        "Return_on_Equity": info.get("returnOnEquity", None),
    }
    return data

def build_dataset(ticker_list):
    all_companies = []
    for ticker in ticker_list:
        print(f"Fetching {ticker}...")
        all_companies.append(get_company_data(ticker))
    return pd.DataFrame(all_companies)


targets = ["AAPL", "MSFT", "GOOGL", "META", "NVDA",
           "ORCL", "CRM", "ADBE", "INTC", "AMD"]

df = build_dataset(targets)
# --- Clean up missing values ---
numeric_cols = ["PE_Ratio", "Profit_Margin", "Revenue_Growth",
                "Debt_to_Equity", "Return_on_Equity"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].fillna(df[col].median())


# --- Score each company as an acquisition target ---
def score_targets(df, weights):
    df = df.copy()

    def normalize(column, invert=False):
        col = df[column]
        if col.max() == col.min():
            return pd.Series(0.5, index=col.index)
        scaled = (col - col.min()) / (col.max() - col.min())
        return 1 - scaled if invert else scaled

    df["s_valuation"] = normalize("PE_Ratio", invert=True)
    df["s_profit"]    = normalize("Profit_Margin")
    df["s_growth"]    = normalize("Revenue_Growth")
    df["s_debt"]      = normalize("Debt_to_Equity", invert=True)
    df["s_roe"]       = normalize("Return_on_Equity")

    df["Target_Score"] = (
        df["s_valuation"] * weights["valuation"] +
        df["s_profit"]    * weights["profit"] +
        df["s_growth"]    * weights["growth"] +
        df["s_debt"]      * weights["debt"] +
        df["s_roe"]       * weights["roe"]
    ) * 100

    return df.sort_values("Target_Score", ascending=False)


# --- Three acquirer scenarios (weights must each sum to 1.0) ---
scenarios = {
    "Growth-Defense": {   # our primary thesis: buying growth & quality
        "valuation": 0.10, "profit": 0.25, "growth": 0.35,
        "debt": 0.10, "roe": 0.20,
    },
    "Value-Disciplined": {  # a cautious buyer hunting cheap, sound assets
        "valuation": 0.35, "profit": 0.20, "growth": 0.10,
        "debt": 0.20, "roe": 0.15,
    },
    "Balance-Sheet-Cautious": {  # prizes financial safety above all
        "valuation": 0.20, "profit": 0.20, "growth": 0.15,
        "debt": 0.35, "roe": 0.10,
    },
}

# Primary ranking uses our chosen thesis
ranked = score_targets(df, scenarios["Growth-Defense"])
print("\n=== PRIMARY RANKING (Growth-Defense thesis) ===")
print(ranked[["Name", "Sector", "Target_Score"]].to_string(index=False))



# --- Translate scores into decision tiers ---
def assign_tier(score):
    if score >= 60:
        return "Tier 1 - Pursue"
    elif score >= 40:
        return "Tier 2 - Monitor"
    else:
        return "Tier 3 - Pass"

ranked["Tier"] = ranked["Target_Score"].apply(assign_tier)

print("\n=== TIERED RECOMMENDATION (Growth-Defense thesis) ===")
print(ranked[["Name", "Target_Score", "Tier"]].to_string(index=False))

# --- Sensitivity analysis: how rankings shift by acquirer type ---
sensitivity = pd.DataFrame({"Name": df["Name"]})

for scenario_name, weights in scenarios.items():
    scored = score_targets(df, weights)
    score_map = dict(zip(scored["Name"], scored["Target_Score"].round(1)))
    sensitivity[scenario_name] = sensitivity["Name"].map(score_map)

for scenario_name in scenarios.keys():
    rank_col = scenario_name + "_Rank"
    sensitivity[rank_col] = sensitivity[scenario_name].rank(ascending=False).astype(int)

print("\n=== SENSITIVITY: SCORES BY ACQUIRER THESIS ===")
print(sensitivity[["Name"] + list(scenarios.keys())].to_string(index=False))

print("\n=== SENSITIVITY: RANK BY ACQUIRER THESIS ===")
rank_cols = ["Name"] + [s + "_Rank" for s in scenarios.keys()]
print(sensitivity[rank_cols].to_string(index=False))


# --- Export a polished multi-sheet Excel report ---
if "Tier" not in ranked.columns:
    ranked["Tier"] = ranked["Target_Score"].apply(assign_tier)

with pd.ExcelWriter("ma_target_report.xlsx", engine="openpyxl") as writer:
    primary = ranked[["Ticker", "Name", "Sector", "Target_Score", "Tier"]].round(1)
    primary.to_excel(writer, sheet_name="Recommendation", index=False)

    financials = ranked[["Ticker", "Name", "Sector", "Market_Cap",
                         "PE_Ratio", "Profit_Margin", "Revenue_Growth",
                         "Debt_to_Equity", "Return_on_Equity"]].round(2)
    financials.to_excel(writer, sheet_name="Financials", index=False)

    sens_scores = sensitivity[["Name"] + list(scenarios.keys())]
    sens_scores.to_excel(writer, sheet_name="Sensitivity_Scores", index=False)

    rank_cols = ["Name"] + [s + "_Rank" for s in scenarios.keys()]
    sens_ranks = sensitivity[rank_cols]
    sens_ranks.to_excel(writer, sheet_name="Sensitivity_Ranks", index=False)

print("\nMulti-sheet report saved to ma_target_report.xlsx")
print("Sheets: Recommendation | Financials | Sensitivity_Scores | Sensitivity_Ranks")
# --- 2x2 strategic matrix: Growth vs. Valuation ---
# Make sure Tier exists (it should, but this keeps the chart self-sufficient)
if "Tier" not in ranked.columns:
    ranked["Tier"] = ranked["Target_Score"].apply(assign_tier)

# Colour each tier distinctly
tier_colors = {
    "Tier 1 - Pursue":  "#2e7d32",   # green
    "Tier 2 - Monitor": "#f9a825",   # amber
    "Tier 3 - Pass":    "#c62828",   # red
}

fig, ax = plt.subplots(figsize=(11, 8))

# Plot each company as a point, coloured by tier
for tier_name, color in tier_colors.items():
    subset = ranked[ranked["Tier"] == tier_name]
    ax.scatter(subset["Revenue_Growth"], subset["PE_Ratio"],
               s=160, c=color, label=tier_name,
               edgecolors="black", linewidths=0.7, zorder=3)

# Label each point with the company ticker
for _, row in ranked.iterrows():
    ax.annotate(row["Ticker"],
                (row["Revenue_Growth"], row["PE_Ratio"]),
                xytext=(6, 6), textcoords="offset points",
                fontsize=9, fontweight="bold")

# Quadrant divider lines (median of each axis)
ax.axvline(ranked["Revenue_Growth"].median(), color="grey",
           linestyle="--", linewidth=1, zorder=1)
ax.axhline(ranked["PE_Ratio"].median(), color="grey",
           linestyle="--", linewidth=1, zorder=1)

# Labels and styling
ax.set_xlabel("Revenue Growth  →  (higher is better)", fontsize=11)
ax.set_ylabel("P/E Ratio  →  (lower is cheaper)", fontsize=11)
ax.set_title("M&A Target Matrix: Growth vs. Valuation\n(Growth-Defense thesis)",
             fontsize=14, fontweight="bold")
ax.legend(title="Recommendation", loc="upper left")
ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig("ma_target_matrix.png", dpi=200)
plt.show()
print("\nChart saved to ma_target_matrix.png")