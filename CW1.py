import pandas as pd
import altair as alt

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

gender_color_scale = alt.Scale(domain=['Male', 'Female'], range=['#347DC1', '#FFC0CB']) # Bright Blue & Pink

year_slider = alt.binding_range(min=1980, max=2016, step=1, name='Year: ')
select_year = alt.selection_point(name="Year", fields=['Year'], bind=year_slider, value=2014)

region_options = [None] + sorted(data['Region'].dropna().unique().tolist())
region_labels = ['All'] + sorted(data['Region'].dropna().unique().tolist())

region_dropdown = alt.binding_select(
    options=region_options, 
    labels=region_labels, 
    name='Region: '
)

select_region = alt.selection_point(
    fields=['Region'], 
    bind=region_dropdown, 
    value=None 
)

scatter_bmi = alt.Chart(data).mark_circle().encode(
    x='Urban_Population:Q',
    y='BMI:Q',
    color='Region:N',
    size='GDP:Q'
).transform_filter(
    select_year 
).transform_filter(
    select_region 
)

line_bmi = alt.Chart(data).mark_line().encode(
    x='Year:O',
    y='mean(BMI):Q',
    color='Gender:N'
).transform_filter(
    select_region # Do NOT add select_year here!
)

final_page = (scatter_bmi | line_bmi).add_params(select_year, select_region)

final_page.save("index.html")