import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

file_path = r"cw1 -dataset.xlsx"

xls = pd.ExcelFile(file_path)

bmi = pd.read_excel(xls, 'BMI')
bp = pd.read_excel(xls, 'Raised Blood Pressure')
diabetes = pd.read_excel(xls, 'Diabetes')

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

print("Column Names: ", diabetes.columns)

data = bmi.merge(bp, on=["Country", "Year", "Gender"], how="outer")
data = data.merge(diabetes, on=["Country", "Year", "Gender"], how="outer")

data = data.dropna(subset=["BMI", "BP", "Diabetes"])

data['Year'] = data['Year'].astype(int)
data['BMI'] = pd.to_numeric(data['BMI'], errors='coerce')
data['BP'] = pd.to_numeric(data['BP'], errors='coerce')
data['Diabetes'] = pd.to_numeric(data['Diabetes'], errors='coerce')

data = data.dropna(subset=["BMI", "BP", "Diabetes"])

data['BMI'] *= 100
data['BP'] *= 100
data['Diabetes'] *= 100

gdp = pd.read_csv("GDP.csv")
income = pd.read_csv("GDP Metadata.csv")
urban_population = pd.read_csv("Urban Population.csv")

gdp = gdp.drop(columns=['GDP per capita (Annotations)'], errors='ignore')
gdp_long = gdp.rename(columns={'Entity': 'Country', 'Code': 'Country Code', 'GDP per capita': 'GDP'})
gdp_long = gdp_long[~gdp_long['Country Code'].str.contains('AFE|AFW', na=False)]
gdp_long['Year'] = pd.to_numeric(gdp_long['Year'], errors='coerce')
gdp_long = gdp_long[(gdp_long['Year'] >= 1980) & (gdp_long['Year'] <= 2016)]

urban_population.rename(columns={
    urban_population.columns[0]: 'Country Name',
    urban_population.columns[1]: 'Country Code'
}, inplace=True)

urban_population = urban_population.drop(
    columns=['Indicator Name', 'Indicator Code', 'Unnamed: 69'],
    errors='ignore'
)
urban_long = urban_population.melt(
    id_vars=['Country Name', 'Country Code'],
    var_name='Year',
    value_name='Urban_Population'
)
urban_long['Year'] = pd.to_numeric(urban_long['Year'], errors='coerce')
urban_long = urban_long[(urban_long['Year'] >= 1980) & (urban_long['Year'] <= 2016)]
urban_long = urban_long.rename(columns={'Country Name': 'Country'})
urban_long.columns

income_clean = income[['Country Code', 'Region', 'IncomeGroup']]

health_countries = set(data['Country'].unique())
urban_countries = set(urban_long['Country'].unique())

missing_in_urban = health_countries - urban_countries
print("Countries in health data not in urban population:", missing_in_urban)

urban_long = urban_population.melt(
    id_vars=['Country Name', 'Country Code'],
    var_name='Year',
    value_name='Urban_Population'
)
urban_long = urban_long.rename(columns={'Country Name': 'Country'})
urban_long['Year'] = pd.to_numeric(urban_long['Year'], errors='coerce')

data = data.merge(
    urban_long[['Country', 'Year', 'Urban_Population']],
    on=['Country', 'Year'],
    how='left'
)

print("Missing Urban Population values:", data['Urban_Population'].isna().sum())
print(data[data['Urban_Population'].isna()][['Country', 'Year']].drop_duplicates())

code_to_country = urban_long[['Country Code', 'Country']].drop_duplicates()


urban_long_clean = urban_long[['Country', 'Year', 'Urban_Population']].copy()
data = data.merge(
    urban_long[['Country', 'Year', 'Urban_Population']],
    on=['Country', 'Year'],
    how='left'
)

if 'Urban_Population_x' in data.columns:
    data['Urban_Population'] = data['Urban_Population_x']
    data = data.drop(columns=['Urban_Population_x', 'Urban_Population_y'], errors='ignore')

print("Columns in health data after adding Urban Population:", data.columns)
print("Missing Urban Population values:", data['Urban_Population'].isna().sum())

print("Columns in health data after adding Urban Population:", data.columns)
print("Missing Urban Population values:", data['Urban_Population'].isna().sum())
print(data[data['Urban_Population'].isna()][['Country', 'Year']].drop_duplicates())

income_clean = income[['Country Code', 'Region', 'IncomeGroup']].copy()
income_clean = income_clean.merge(
    code_to_country,  
    on='Country Code',
    how='left'
)
print("Income sample after merge:")
print(income_clean[['Country Code', 'Country', 'Region', 'IncomeGroup']].head())
gdp_long = gdp_long[~gdp_long['Country Code'].str.contains('AFE|AFW|AFR|EAS|OCE', na=False)]

gdp_long['Country Code'] = gdp_long['Country Code'].str.strip()
code_to_country['Country Code'] = code_to_country['Country Code'].str.strip()

gdp_long = gdp_long.merge(
    code_to_country[['Country Code', 'Country']], 
    on='Country Code', 
    how='left'
)
if 'Country_y' in gdp_long.columns:
    gdp_long['Country'] = gdp_long['Country_y']
    gdp_long = gdp_long.drop(columns=['Country_x', 'Country_y'], errors='ignore')

gdp_long.loc[gdp_long['Country Code']=='TWN', 'Country'] = 'Taiwan'

print(gdp_long[['Country Code', 'Country', 'Year', 'GDP']].head())

missing_gdp = gdp_long[gdp_long['Country'].isna()]['Country Code'].unique()
missing_income = income_clean[income_clean['Country'].isna()]['Country Code'].unique()

print("Missing GDP countries:", missing_gdp)
print("Missing Income countries:", missing_income)

data = data.merge(
    gdp_long[['Country', 'Year', 'GDP']],
    on=['Country', 'Year'],
    how='left'
)

data = data.merge(
    income_clean[['Country', 'Region', 'IncomeGroup']],
    on='Country',
    how='left'
)

if 'Urban_Population_x' in data.columns:
    data['Urban_Population'] = data['Urban_Population_x']
    data = data.drop(columns=['Urban_Population_x', 'Urban_Population_y'], errors='ignore')

print("Columns in final master dataframe:")
print(data.columns)
print("Sample rows:")
print(data.head())

print("Missing values per column:")
print(data[['BMI', 'BP', 'Diabetes', 'Urban_Population', 'GDP', 'Region', 'IncomeGroup']].isna().sum())

data['IncomeGroup'] = data['IncomeGroup'].fillna("Not Classified")
print(data.isna().sum().sort_values(ascending=False))

missing_gdp_counts = (
    data[data['GDP'].isna()]
    .groupby('Country')
    .size()
    .sort_values(ascending=False)
)

print(missing_gdp_counts.head(50))

print(data[(data['Country'] == 'United Arab Emirates') & (data['GDP'].isna())][['Year', 'Gender']])
print(gdp_long[gdp_long['Country'] == 'United Arab Emirates'][['Year', 'GDP']].sort_values('Year'))

data = data.dropna(subset=['GDP', "Region", "Urban_Population"])

print(data.isna().sum().sort_values(ascending=False))

print(data.columns)

@alt.theme.register('cyberpunk_dark', enable=True)
def cyberpunk_theme():
    return alt.theme.ThemeConfig({
        'config': {
            'background': '#2b2b2b',  # Your dark grey background
            'view': {'stroke': 'transparent'},
            'axis': {
                'domainColor': '#FFFFFF', # White axes
                'gridColor': '#444444',   # Subtle grid lines
                'labelColor': '#FFFFFF',
                'titleColor': '#FFFFFF',
                'tickColor': '#FFFFFF'
            },
            'legend': {
                'labelColor': '#FFFFFF',
                'titleColor': '#FFFFFF'
            },
            'title': {
                'color': '#FFFFFF',
                'fontSize': 18
            },
            'mark': {
                'tooltip': True
            }
        }
    })

gender_scale = alt.Scale(domain=['Male', 'Female'], range=['#347DC1', '#FFC0CB']) # Bright Blue & Pink

year_slider = alt.binding_range(min=1980, max=2016, step=1, name='Year: ')
select_year = alt.selection_point(name="Year", fields=['Year'], bind=year_slider, value=2014)


region_options = [None] + sorted(data['Region'].dropna().unique().tolist())
region_labels = ['All'] + sorted(data['Region'].dropna().unique().tolist())

select_region = alt.selection_point(
    fields=['Region'], 
    bind=alt.binding_select(options=region_options, labels=region_labels, name='Region: '),
    value=None
)

select_year = alt.selection_point(
    fields=['Year'], 
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '),
    value=2010
)

title_header = alt.Chart(pd.DataFrame({'t': ["Global Health & Wealth Insights 1980–2016"]})).mark_text(
    align='left', baseline='middle', fontSize=28, fontWeight='bold', color='#00D4FF', dx=-200
).encode(text='t:N').properties(width=800, height=50)

kpi_obesity = alt.Chart(data).mark_text(fontSize=40, fontWeight='bold', color='#FF007F').encode(
    text=alt.Text('mean(BMI):Q', format='.1f')
).transform_filter(
    select_region & select_year
).properties(width=200, height=100, title="Avg. Obesity %")

kpi_gdp = alt.Chart(data).mark_text(fontSize=40, fontWeight='bold', color='#00D4FF').encode(
    text=alt.Text('mean(GDP):Q', format='$,.0f')
).transform_filter(
    select_region & select_year
).properties(width=200, height=100, title="Avg. GDP per Capita")

kpi_urban = alt.Chart(data).mark_text(fontSize=40, fontWeight='bold', color='#32CD32').encode(
    text=alt.Text('mean(Urban_Population):Q', format='.1f')
).transform_filter(
    select_region & select_year
).properties(width=200, height=100, title="Avg. Urbanization %")

kpi_row = alt.hconcat(kpi_obesity, kpi_gdp, kpi_urban)

header_section = alt.vconcat(title_header, kpi_row).configure_view(stroke=None)

scatter = alt.Chart(data).mark_circle().encode(
    x=alt.X('Urban_Population:Q', title='Urban Population (%)'),
    y=alt.Y('BMI:Q', title='BMI Prevalence'),
    color=alt.Color('Region:N', legend=alt.Legend(title="Region")),
    size=alt.Size('GDP:Q', legend=alt.Legend(title="GDP per Capita")),
    tooltip=['Country', 'BMI', 'Urban_Population']
).transform_filter(
    select_region & select_year
).properties(width=400, height=350, title="Urbanization vs Obesity")


line = alt.Chart(data).mark_line().encode(
    x='Year:O',
    y='mean(BMI):Q',
    color=alt.Color('Gender:N', scale=gender_scale, legend=alt.Legend(title="Gender")), 
).transform_filter(
    select_region # Only filter by region here, DO NOT add select_year!
).properties(width=400, height=350, title="BMI Trend Over Time")

# 1. Combine your KPI text marks horizontally
kpi_row = alt.hconcat(kpi_obesity, kpi_gdp, kpi_urban).resolve_scale(color='independent')

# 2. Combine your scatter and line charts horizontally
bottom_row = alt.hconcat(scatter, line).resolve_scale(color='independent', size='independent')

# 3. Stack the header, KPIs, and charts vertically into ONE master chart
master_page = alt.vconcat(
    title_header,
    kpi_row,
    bottom_row
).add_params(
    select_region, select_year # Add the filters to the master container!
).configure_view(
    stroke=None 
).configure_concat(
    spacing=30 # Adds nice breathing room between your charts
)

# 4. Export the single master JSON
master_json = master_page.to_json()

# Using double {{ }} for CSS/JS so the f-string only populates {master_json}
html_template = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body {{ 
      background-color: #2b2b2b;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
      color: white; 
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px;
    }}
    #filters {{ 
      background: #3d3d3d; 
      padding: 15px 25px; 
      border-radius: 12px; 
      border: 1px solid #555;
      margin-bottom: 30px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .vega-bind {{ color: white !important; font-size: 14px; margin-right: 20px; }}
    .vega-bind-name {{ font-weight: bold; color: #00D4FF; }}
  </style>
</head>
<body>
    <div id="filters"></div> 
    <div id="dashboard"></div>

  <script>
    const spec = {master_json};
    const opt = {{ "bind": "#filters", "actions": false }};
    vegaEmbed('#dashboard', spec, opt).catch(console.error);
  </script>
</body>
</html>
"""

# 3. Save to file
with open("Tiled_Health_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("Tiled Dashboard saved! Solid #2b2b2b background with #3d3d3d tiles is ready.")