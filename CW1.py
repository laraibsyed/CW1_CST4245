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

data['GDP'] = pd.to_numeric(data['GDP'], errors='coerce')
data['Urban_Population'] = pd.to_numeric(data['Urban_Population'], errors='coerce')

print(data.columns)


@alt.theme.register('cyberpunk_dark', enable=True)
def cyberpunk_theme():
    return alt.theme.ThemeConfig({
        'config': {
            'background': '#2b2b2b',  
            'view': {'stroke': 'transparent'},
            'axis': {
                'domainColor': '#FFFFFF', 
                'gridColor': '#444444',   
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
            'mark': {'tooltip': True}
        }
    })

gender_scale = alt.Scale(domain=['Men', 'Women'], range=['#347DC1', '#FFC0CB']) 

region_options = [None] + sorted(data['Region'].dropna().unique().tolist())
region_labels = ['All'] + sorted(data['Region'].dropna().unique().tolist())

select_region = alt.selection_point(
    fields=['Region'], 
    bind=alt.binding_select(options=region_options, labels=region_labels, name='Region: ')
)

select_year = alt.selection_point(
    name="Year", 
    fields=['Year'], 
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '), 
    value=2014
)

yearly_global = data.groupby('Year')[['BMI', 'BP', 'Diabetes']].mean().sort_values('Year').reset_index()
yearly_global['Highest_Risk'] = yearly_global[['BMI', 'BP', 'Diabetes']].idxmax(axis=1)

prev_year = yearly_global.set_index('Year')[['BMI', 'BP', 'Diabetes']].shift(1).reset_index()
yearly_global = yearly_global.merge(prev_year, on='Year', suffixes=('', '_prev'))

def build_trend_text(row):
    risk = row['Highest_Risk']
    curr_val = row[risk]
    prev_val = row[f"{risk}_prev"]
    
    if pd.isna(prev_val): 
        return f"📈 {risk} (Base Year: {curr_val:.1f}%)"
    
    diff = curr_val - prev_val
    sign = "+" if diff > 0 else ""
    return f"📈 {risk} ({sign}{diff:.1f}% vs prev yr)"

yearly_global['Trend_Text'] = yearly_global.apply(build_trend_text, axis=1)
data = data.merge(yearly_global[['Year', 'Trend_Text']], on='Year', how='left')


title_header = alt.Chart(pd.DataFrame({'t': ["Global Health & Wealth Insights 1980–2016"]})).mark_text(
    align='left', baseline='middle', fontSize=28, fontWeight='bold', color='#00D4FF', dx=-200
).encode(text='t:N').properties(width=800, height=50)

kpi_bmi = alt.Chart(data).mark_text(fontSize=32, fontWeight='bold', color='#FF007F').encode(
    text=alt.Text('mean(BMI):Q', format='.1f')
).transform_filter(select_region & select_year).properties(width=135, height=80, title="Avg Obesity %")

kpi_bp = alt.Chart(data).mark_text(fontSize=32, fontWeight='bold', color='#FF8C00').encode(
    text=alt.Text('mean(BP):Q', format='.1f')
).transform_filter(select_region & select_year).properties(width=135, height=80, title="Avg High BP %")

kpi_diabetes = alt.Chart(data).mark_text(fontSize=32, fontWeight='bold', color='#9400D3').encode(
    text=alt.Text('mean(Diabetes):Q', format='.1f')
).transform_filter(select_region & select_year).properties(width=135, height=80, title="Avg Diabetes %")

kpi_risk_country = alt.Chart(data).transform_filter(
    select_region & select_year 
).transform_aggregate(
    risk_score='mean(BMI)', groupby=['Country']
).transform_window(
    rank='rank()', sort=[alt.SortField('risk_score', order='descending')]
).transform_filter(
    'datum.rank == 1'
).mark_text(fontSize=14, fontWeight='bold', color='#FF4500', align='center', dy=5).encode(
    text='Country:N'
).properties(width=135, height=80, title="Highest BMI Country")

kpi_countries = alt.Chart(data).mark_text(fontSize=32, fontWeight='bold', color='#00D4FF').encode(
    text=alt.Text('distinct(Country):Q') 
).transform_filter(select_region & select_year).properties(width=135, height=80, title="Countries Included")

kpi_trend = alt.Chart(data).mark_text(
    fontSize=14, fontWeight='bold', color='#32CD32', align='center', dy=5
).encode(
    text='Trend_Text:N'
).transform_filter(select_year).transform_aggregate(
    groupby=['Trend_Text'] 
).properties(width=180, height=80, title="Top Global Risk (YoY)")

kpi_row = alt.hconcat(
    kpi_bmi, kpi_bp, kpi_diabetes, kpi_risk_country, kpi_countries, kpi_trend
).resolve_scale(color='independent')


multi_line = alt.Chart(data).transform_filter(
    select_region
).transform_fold(
    ['BMI', 'BP', 'Diabetes'],
    as_=['Metric', 'Prevalence']
).mark_line(
    point=True, strokeWidth=3, interpolate='monotone' 
).encode(
    x=alt.X('Year:Q', axis=alt.Axis(format='d', grid=False), title='Year'), 
    y=alt.Y('mean(Prevalence):Q', title='Avg Prevalence %', scale=alt.Scale(zero=False)),
    color=alt.Color('Metric:N', scale=alt.Scale(
        domain=['BMI', 'BP', 'Diabetes'],
        range=['#FF007F', '#FF8C00', '#9400D3'] 
    ), legend=alt.Legend(title="Health Metric", orient='top-left')),
    tooltip=[
        alt.Tooltip('Year:Q', title='Year'), 
        alt.Tooltip('Metric:N', title='Metric'), 
        alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Avg %')
    ]
).properties(width=400, height=350, title="Global Health Risks Over Time")

tracker = alt.Chart(data).mark_rule(
    color='#00D4FF', 
    strokeWidth=2,
    strokeDash=[5, 5], 
    opacity=0.8
).encode(
    x='Year:Q'
).transform_filter(
    select_year 
)

interactive_multi_line = multi_line + tracker

snapshot = alt.Chart(data).transform_filter(
    select_region 
).transform_filter(
    select_year 
).transform_fold(
    ['BMI', 'BP', 'Diabetes'],
    as_=['Metric', 'Prevalence']
).mark_bar(
    cornerRadiusTopLeft=5,
    cornerRadiusTopRight=5,
    stroke='#00D4FF',
    strokeWidth=0.5
).encode(
    x=alt.X('Metric:N', title='Health Metric', axis=alt.Axis(labelAngle=0, grid=False)), 
    y=alt.Y('mean(Prevalence):Q', title='Global Average %', scale=alt.Scale(domain=[0, 30])), 
    color=alt.Color('Metric:N', scale=alt.Scale(
        domain=['BMI', 'BP', 'Diabetes'],
        range=['#FF007F', '#FF8C00', '#9400D3'] 
    ), legend=None), 
    tooltip=[
        alt.Tooltip('Metric:N', title='Metric'), 
        alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Avg %')
    ]
).properties(
    width=400, 
    height=350, 
    title="Global Snapshot (Selected Year)"
)

snapshot_labels = snapshot.mark_text(
    align='center',
    baseline='bottom',
    dy=-5, 
    color='white',
    fontWeight='bold',
    fontSize=14
).encode(
    text=alt.Text('mean(Prevalence):Q', format='.1f')
)

final_snapshot = (snapshot + snapshot_labels).resolve_scale(color='independent')

top_10_countries = alt.Chart(data).transform_filter(
    select_region
).transform_filter(
    select_year
).transform_aggregate(
    avg_bmi='mean(BMI)',
    groupby=['Country']
).transform_window(
    rank='rank()',
    sort=[alt.SortField('avg_bmi', order='descending')]
).transform_filter(
    alt.datum.rank <= 10 
).mark_bar(
    cornerRadiusTopRight=5,
    cornerRadiusBottomRight=5,
    color='#FF4500', 
).encode(
    x=alt.X('avg_bmi:Q', title='Average Obesity (%)', axis=alt.Axis(grid=True)),
    y=alt.Y('Country:N', sort=alt.EncodingSortField(field='avg_bmi', order='descending'), title=None),
    tooltip=[
        alt.Tooltip('rank:O', title='Global Rank'),
        alt.Tooltip('Country:N', title='Country'),
        alt.Tooltip('avg_bmi:Q', format='.1f', title='Obesity %')
    ]
).properties(
    width=450,
    height=alt.Step(20), 
    title="Top 10 Highest Risk Countries (Selected Year)"
)
top_10_labels = top_10_countries.mark_text(
    align='left',
    baseline='middle',
    dx=5,
    color='white',
    fontWeight='bold',
    fontSize=12
).encode(
    text=alt.Text('avg_bmi:Q', format='.1f')
)

final_top_10 = (top_10_countries + top_10_labels)

gender_bars = alt.Chart(data).transform_filter(
    select_region
).transform_filter(
    select_year
).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(
    ['BMI', 'BP', 'Diabetes'],
    as_=['Metric', 'Prevalence']
).mark_bar(
    cornerRadiusTopLeft=4,
    cornerRadiusTopRight=4,
    stroke='#2b2b2b', 
    strokeWidth=1
).encode(
    x=alt.X('Metric:N', title='Health Metric', axis=alt.Axis(labelAngle=0, grid=False)),
    
    xOffset=alt.XOffset('Gender:N', sort=['Men', 'Women']), 
    
    y=alt.Y('mean(Prevalence):Q', title='Global Average %'),
    
    color=alt.Color('Gender:N', scale=gender_scale, legend=alt.Legend(
        title=None, 
        orient='top-right',
        offset=-10 
    )),
    tooltip=[
        alt.Tooltip('Gender:N', title='Demographic'),
        alt.Tooltip('Metric:N', title='Health Risk'),
        alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Avg %')
    ]
).properties(
    width=320, 
    height=240, 
    title="Gender Disparity (Selected Year)"
)

gender_labels = gender_bars.mark_text(
    align='center',
    baseline='bottom',
    dy=-3,
    color='white',
    fontSize=11,
    fontWeight='bold'
).encode(
    text=alt.Text('mean(Prevalence):Q', format='.1f')
)

final_gender_chart = (gender_bars + gender_labels)

middle_row = alt.hconcat(
    final_snapshot,         
    interactive_multi_line  
).resolve_scale(color='independent')

bottom_floor = alt.hconcat(
    final_top_10,
    final_gender_chart
).resolve_scale(color='independent')

# ==========================================
# 🏗️ PAGE 1: OVERVIEW (Your Current Masterpiece)
# ==========================================
page_overview = alt.vconcat(
    title_header, kpi_row, middle_row, bottom_floor
).add_params(select_region, select_year).configure_view(stroke=None).configure_concat(spacing=40)

overview_json = page_overview.to_json()


# ── PAGE 2 FRESH SIGNALS ─────────────────────────────────────────────
select_region_2 = alt.selection_point(
    name="region_p2",
    fields=['Region'],
    bind=alt.binding_select(options=region_options, labels=region_labels, name='Region: ')
)
select_year_2 = alt.selection_point(
    name="year_p2",
    fields=['Year'],
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '),
    value=2014
)

# ── ALL PAGE 2 CHARTS (every single one rebuilt fresh) ────────────────
socio_title = alt.Chart(pd.DataFrame({'t': ["Socioeconomic Risk Analysis"]})).mark_text(
    align='left', fontSize=28, fontWeight='bold', color='#00D4FF'
).encode(text='t:N').properties(width=800, height=50)

kpi_gdp = alt.Chart(data).mark_text(
    fontSize=40, fontWeight='bold', color='#00FF9F', align='center'
).encode(
    text=alt.Text('mean(GDP):Q', format='$,.0f')
).transform_filter(
    select_region_2 & select_year_2
).properties(width=250, height=100, title="Avg GDP per Capita")

kpi_urban = alt.Chart(data).mark_text(
    fontSize=40, fontWeight='bold', color='#B026FF', align='center'
).encode(
    text=alt.Text('mean(Urban_Population):Q', format='.1f')
).transform_filter(
    select_region_2 & select_year_2
).properties(width=250, height=100, title=alt.TitleParams(text="Avg Urbanisation %", color='#FFFFFF', fontSize=14))

kpi_gender_risk = alt.Chart(data).transform_filter(
    select_region_2 & select_year_2
).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_aggregate(
    avg_bmi='mean(BMI)',
    avg_bp='mean(BP)',
    avg_diabetes='mean(Diabetes)',
    groupby=['Gender']
).transform_calculate(
    total_risk="datum.avg_bmi + datum.avg_bp + datum.avg_diabetes"
).transform_window(
    rank='rank()',
    sort=[alt.SortField('total_risk', order='descending')]
).transform_filter(
    'datum.rank == 1'
).mark_text(
    fontSize=28, fontWeight='bold', align='center', dy=10
).encode(
    text='Gender:N',
    color=alt.Color('Gender:N', scale=gender_scale, legend=None)
).properties(width=180, height=80, title=alt.TitleParams(text="Highest Overall Risk", color='#FFFFFF'))

boxplot_socio = alt.Chart(data).transform_filter(
    select_region_2 & select_year_2
).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
).mark_boxplot(
    size=30, extent='min-max', outliers=alt.MarkConfig(size=15, opacity=0.6, color='#00D4FF')
).encode(
    x=alt.X('IncomeGroup:N', title='Income Group', sort=['High income', 'Upper middle income', 'Lower middle income', 'Low income']),
    y=alt.Y('Prevalence:Q', title='Prevalence (%)', scale=alt.Scale(zero=False)),
    color=alt.Color('Gender:N', scale=gender_scale),
    xOffset=alt.XOffset('Gender:N'),
    tooltip=['IncomeGroup:N', 'Gender:N', 'Country:N', alt.Tooltip('Prevalence:Q', format='.1f')]
).properties(width=750, height=350, title="Health Distribution by Income & Gender")

# ── HEATMAP (static, no signals needed) ──────────────────────────────
corr_cols = ['BMI', 'BP', 'Diabetes', 'GDP', 'Urban_Population']
corr_matrix = data[corr_cols].corr().reset_index().melt(id_vars='index')
corr_matrix.columns = ['Var1', 'Var2', 'Correlation']

heatmap = alt.Chart(corr_matrix).mark_rect().encode(
    x=alt.X('Var1:N', title=None),
    y=alt.Y('Var2:N', title=None),
    color=alt.Color('Correlation:Q',
                    scale=alt.Scale(scheme='viridis', domain=[-1, 1]),
                    legend=alt.Legend(title="Pearson Corr")),
    tooltip=[alt.Tooltip('Var1:N'), alt.Tooltip('Var2:N'), alt.Tooltip('Correlation:Q', format='.2f')]
).properties(width=350, height=350, title="Socioeconomic & Health Correlations")

heatmap_text = heatmap.mark_text(baseline='middle').encode(
    text=alt.Text('Correlation:Q', format='.2f'),
    color=alt.condition(alt.datum.Correlation > 0.5, alt.value('black'), alt.value('white'))
)
final_heatmap = (heatmap + heatmap_text)

# ── ASSEMBLE ──────────────────────────────────────────────────────────
kpi_row_2 = alt.hconcat(
    kpi_gdp, kpi_urban, kpi_gender_risk
).resolve_scale(color='independent')

page_socio = alt.vconcat(
    socio_title,
    kpi_gdp, kpi_urban
).add_params(
    select_region_2, select_year_2  # ← ONLY page 2 signals here
).configure_view(stroke=None).configure_concat(spacing=40)

# ── SAVE AS SEPARATE HTML ─────────────────────────────────────────────
page_socio.save('page2_socio.html')
socio_json = page_socio.to_json()
print("Page 2 saved ✅")

# ==========================================
# 🏗️ PAGE 3: REGIONAL RISK (Placeholder)
# ==========================================
placeholder_text_3 = alt.Chart(pd.DataFrame({'t': ["Regional Risk Matrix Offline."]})).mark_text(
    fontSize=30, color='#9400D3'
).encode(text='t:N').properties(width=800, height=400)

page_regional = alt.vconcat(placeholder_text_3).configure_view(stroke=None)
regional_json = page_regional.to_json()
# ==========================================
# 🌐 HTML EXPORT (THE TABBED SPA - SLEDGEHAMMER EDITION)
html_template = f"""<!DOCTYPE html>
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
      padding: 20px;
    }}
    .nav-bar {{
      display: flex;
      gap: 15px;
      margin-bottom: 30px;
      background: #1a1a1a;
      padding: 10px 20px;
      border-radius: 8px;
      border: 1px solid #444;
      box-shadow: 0 4px 15px rgba(0,212,255,0.2);
    }}
    .tab-btn {{
      background: transparent;
      color: #aaa;
      border: 2px solid transparent;
      padding: 10px 20px;
      font-size: 16px;
      font-weight: bold;
      border-radius: 5px;
      cursor: pointer;
      transition: all 0.3s ease;
    }}
    .tab-btn:hover {{ color: white; border-color: #555; }}
    .tab-btn.active {{
      color: #00D4FF;
      border-color: #00D4FF;
      text-shadow: 0 0 8px rgba(0,212,255,0.6);
      box-shadow: inset 0 0 10px rgba(0,212,255,0.2);
    }}
    .dashboard-page {{ 
      display: none;
      flex-direction: column; 
      align-items: center; 
      width: 100%;
    }}
    .dashboard-page.active {{ 
      display: flex;
    }}
    .filter-box {{ 
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

  <div class="nav-bar">
    <button class="tab-btn active" onclick="switchTab('overview', this)">1. Overview</button>
    <button class="tab-btn" onclick="switchTab('socio', this)">2. Socioeconomic</button>
    <button class="tab-btn" onclick="switchTab('regional', this)">3. Regional Risk</button>
  </div>

  <div id="page-overview" class="dashboard-page active">
    <div id="filters-overview" class="filter-box"></div>
    <div id="vis-overview"></div>
  </div>
  <div id="page-socio" class="dashboard-page">
    <div id="filters-socio" class="filter-box"></div>
    <div id="vis-socio"></div>
  </div>
  <div id="page-regional" class="dashboard-page">
    <div id="filters-regional" class="filter-box"></div>
    <div id="vis-regional"></div>
  </div>

  <!-- Each spec stored as a raw string in its own script tag -->
  <script type="application/json" id="spec-overview">{overview_json}</script>
  <script type="application/json" id="spec-socio">{socio_json}</script>
  <script type="application/json" id="spec-regional">{regional_json}</script>

  <script>
    // Read specs lazily from DOM — Vega never sees them until embedTab is called
    function getSpec(tabName) {{
      return JSON.parse(document.getElementById('spec-' + tabName).textContent);
    }}

    let currentView = null;

    async function embedTab(tabName) {{
      // Destroy previous runtime completely
      if (currentView) {{
        currentView.finalize();
        currentView = null;
      }}

      // Clear all vis and filter containers
      ['overview', 'socio', 'regional'].forEach(t => {{
        document.getElementById('vis-' + t).innerHTML = '';
        document.getElementById('filters-' + t).innerHTML = '';
      }});

      // Parse spec fresh from DOM only at this moment
      const spec = getSpec(tabName);

      const result = await vegaEmbed(
        '#vis-' + tabName,
        spec,
        {{ actions: false, bind: '#filters-' + tabName }}
      );
      currentView = result.view;
    }}

    async function switchTab(tabName, btn) {{
      document.querySelectorAll('.dashboard-page').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('page-' + tabName).classList.add('active');
      btn.classList.add('active');
      await embedTab(tabName);
      window.dispatchEvent(new Event('resize'));
    }}

    // Only embed page 1 on load
    embedTab('overview');
  </script>

</body>
</html>"""

with open("Health_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("Dashboard saved ✅")

import json, re

spec_str = json.dumps(json.loads(socio_json))
all_params = re.findall(r'"name":\s*"([^"]*p2[^"]*)"', spec_str)
print("All p2 param definitions:")
for s in all_params:
    print(s)
print("\nTotal:", len(all_params))

all_tuple = re.findall(r'"name":\s*"([^"]*tuple[^"]*)"', spec_str)
print("All tuple signals:")
for s in all_tuple:
    print(s)
print("\nTotal:", len(all_tuple))