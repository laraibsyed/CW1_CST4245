import pandas as pd

# ── LOAD RAW FILES ─────────────────────────────────────────────────────
xls = pd.ExcelFile(r"cw1 -dataset.xlsx")

bmi      = pd.read_excel(xls, 'BMI')
bp       = pd.read_excel(xls, 'Raised Blood Pressure')
diabetes = pd.read_excel(xls, 'Diabetes')

# ── RENAME HEALTH SHEETS ───────────────────────────────────────────────
bmi = bmi.rename(columns={
    "Country/Region/World": "Country",
    "Sex": "Gender",
    "Prevalence of BMI>=30 kg/m≤ (obesity)": "BMI"
})

bp = bp.rename(columns={
    "Country/Region/World": "Country",
    "Sex": "Gender",
    "Prevalence of raised blood pressure": "BP"
})

diabetes = diabetes.rename(columns={
    "Country/Region/World": "Country",
    "Sex": "Gender",
    "Age-standardised diabetes prevalence": "Diabetes"
})

# ── MERGE & CLEAN HEALTH DATA ──────────────────────────────────────────
data = (
    bmi
    .merge(bp,       on=["Country", "Year", "Gender"], how="outer")
    .merge(diabetes, on=["Country", "Year", "Gender"], how="outer")
)

# Drop rows only where ALL THREE health metrics are missing
data = data.dropna(subset=["BMI", "BP", "Diabetes"])

data["Year"]    = data["Year"].astype(int)
data["BMI"]     = pd.to_numeric(data["BMI"],     errors="coerce") * 100
data["BP"]      = pd.to_numeric(data["BP"],      errors="coerce") * 100
data["Diabetes"]= pd.to_numeric(data["Diabetes"],errors="coerce") * 100

# Drop any rows where conversion left a null in a health metric
data = data.dropna(subset=["BMI", "BP", "Diabetes"])

# ── LOAD & CLEAN GDP ───────────────────────────────────────────────────
gdp_long = (
    pd.read_csv("GDP.csv")
    .drop(columns=["GDP per capita (Annotations)"], errors="ignore")
    .rename(columns={"Entity": "Country", "Code": "Country Code", "GDP per capita": "GDP"})
)

# Remove aggregate/regional codes that aren't individual countries
gdp_long = gdp_long[
    ~gdp_long["Country Code"].str.contains("AFE|AFW|AFR|EAS|OCE", na=False)
]

gdp_long["Year"] = pd.to_numeric(gdp_long["Year"], errors="coerce")
gdp_long = gdp_long[(gdp_long["Year"] >= 1980) & (gdp_long["Year"] <= 2016)]
gdp_long["Country Code"] = gdp_long["Country Code"].str.strip()

# ── LOAD & CLEAN URBAN POPULATION ─────────────────────────────────────
urban_raw = pd.read_csv("Urban Population.csv")
urban_raw = urban_raw.rename(columns={
    urban_raw.columns[0]: "Country",
    urban_raw.columns[1]: "Country Code"
}).drop(columns=["Indicator Name", "Indicator Code", "Unnamed: 69"], errors="ignore")

urban_long = urban_raw.melt(
    id_vars=["Country", "Country Code"],
    var_name="Year",
    value_name="Urban_Population"
)
urban_long["Year"] = pd.to_numeric(urban_long["Year"], errors="coerce")
urban_long = urban_long[(urban_long["Year"] >= 1980) & (urban_long["Year"] <= 2016)]
urban_long["Country Code"] = urban_long["Country Code"].str.strip()

# Shared Country Code → Country name lookup (used for GDP and Income joins)
code_to_country = (
    urban_long[["Country Code", "Country"]]
    .drop_duplicates()
)

# ── LOAD & CLEAN INCOME / REGION METADATA ─────────────────────────────
income_clean = (
    pd.read_csv("GDP Metadata.csv")[["Country Code", "Region", "IncomeGroup"]]
    .copy()
)
income_clean["Country Code"] = income_clean["Country Code"].str.strip()
income_clean = income_clean.merge(code_to_country, on="Country Code", how="left")

# ── MAP COUNTRY NAMES ONTO GDP ─────────────────────────────────────────
gdp_long = gdp_long.merge(
    code_to_country[["Country Code", "Country"]],
    on="Country Code",
    how="left"
)
# Prefer the World Bank country name; fall back to the original if no match
gdp_long["Country"] = gdp_long["Country_y"].fillna(gdp_long["Country_x"])
gdp_long = gdp_long.drop(columns=["Country_x", "Country_y"])

# Manual fix for Taiwan (not in World Bank country list)
gdp_long.loc[gdp_long["Country Code"] == "TWN", "Country"] = "Taiwan"

# ── MERGE EVERYTHING INTO MASTER DATAFRAME ────────────────────────────
data = (
    data
    .merge(urban_long[["Country", "Year", "Urban_Population"]], on=["Country", "Year"], how="left")
    .merge(gdp_long[["Country",  "Year", "GDP"]],               on=["Country", "Year"], how="left")
    .merge(income_clean[["Country", "Region", "IncomeGroup"]],  on="Country",           how="left")
)

# Fill missing region label with "Islands" (countries not in World Bank mapping)
data["Region"] = data["Region"].fillna("Islands")

# Fill missing income group label (keep Region/GDP/Urban as NaN — do NOT drop)
data["IncomeGroup"] = data["IncomeGroup"].fillna("Not Classified")

data["GDP"]              = pd.to_numeric(data["GDP"],              errors="coerce")
data["Urban_Population"] = pd.to_numeric(data["Urban_Population"], errors="coerce")

# ── DIAGNOSTICS ───────────────────────────────────────────────────────
print("Final shape:", data.shape)
print("\nMissing values per column:")
print(data.isna().sum().sort_values(ascending=False))
print("\nSample rows:")
print(data.head())

# ── SAVE ──────────────────────────────────────────────────────────────
data.to_pickle("final_code/clean_data.pkl")
print("\nData saved ✅")