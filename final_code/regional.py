import pandas as pd
import altair as alt

# Load the cleaned data
data = pd.read_pickle("final_code/clean_data.pkl")
alt.data_transformers.disable_max_rows()

# --- THEME CONFIGURATION ---
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
                'fontSize': 18,
                'anchor': 'middle'
            },
            'mark': {'tooltip': True}
        }
    })

# --- SCALES & SELECTIONS ---
gender_scale = alt.Scale(domain=['Men', 'Women'], range=['#347DC1', '#FFC0CB'])

# Filters: Health Metric + Year
metric_bind = alt.binding_select(options=['BMI', 'BP', 'Diabetes'], name='Health Metric: ')
select_metric = alt.selection_point(fields=['Metric'], bind=metric_bind, value='BMI', name="metric_filter")

select_year = alt.selection_point(
    name="year_regional",
    fields=['Year'],
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '),
    value=2014
)

# ── TITLE ─────────────────────────────────────────────────────────────
regional_title = alt.Chart(pd.DataFrame({'t': ["Regional Risk Analysis"]})).mark_text(
    align='center', fontSize=28, fontWeight='bold', color='#00D4FF'
).encode(text='t:N').properties(width=1100, height=50)

# ── KPI HELPERS ───────────────────────────────────────────────────────
# We pre-compute fastest growing, most improved, gender gap outside vega transforms
# because multi-step window + grouped subtraction is hard in Vega transforms alone.

# Fastest growing region: (latest avg prevalence) - (earliest avg prevalence) per region, for each metric
def regional_growth(df, metric):
    g = df[df['Gender'].isin(['Men', 'Women'])].groupby(['Region', 'Year'])[metric].mean().reset_index()
    earliest = g.loc[g.groupby('Region')['Year'].idxmin()].rename(columns={metric: 'early'})
    latest   = g.loc[g.groupby('Region')['Year'].idxmax()].rename(columns={metric: 'late'})
    merged = earliest[['Region', 'early']].merge(latest[['Region', 'late']], on='Region')
    merged['growth'] = merged['late'] - merged['early']
    return merged

growth_bmi      = regional_growth(data, 'BMI');      growth_bmi['Metric']      = 'BMI'
growth_bp       = regional_growth(data, 'BP');        growth_bp['Metric']       = 'BP'
growth_diabetes = regional_growth(data, 'Diabetes');  growth_diabetes['Metric'] = 'Diabetes'
growth_df = pd.concat([growth_bmi, growth_bp, growth_diabetes])

# Gender gap per region/year/metric
def gender_gap(df, metric, year):
    g = df[(df['Year'] == year) & df['Gender'].isin(['Men', 'Women'])].groupby(['Region', 'Gender'])[metric].mean().unstack('Gender').reset_index()
    if 'Men' in g.columns and 'Women' in g.columns:
        g['gap'] = (g['Men'] - g['Women']).abs()
    else:
        g['gap'] = 0
    return g[['Region', 'gap']]

# Build static lookup tables for KPIs — we'll embed them as inline data
# and filter by metric using Vega transforms

# --- KPI: Highest Risk (by region, avg across genders, for selected metric/year) ---
# We fold the data and compute per-region averages, then pick the top region
kpi_base = alt.Chart(data).transform_filter(select_year).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(select_metric)

kpi_highest = kpi_base.transform_aggregate(
    avg_prev='mean(Prevalence)', groupby=['Region']
).transform_window(
    rank='rank()', sort=[alt.SortField('avg_prev', order='descending')]
).transform_filter('datum.rank == 1').mark_text(
    fontSize=20, fontWeight='bold', color='#FF4D4D'
).encode(text='Region:N').properties(width=210, height=100, title="Highest Risk Region")

# --- KPI: Lowest Risk ---
kpi_lowest = kpi_base.transform_aggregate(
    avg_prev='mean(Prevalence)', groupby=['Region']
).transform_window(
    rank='rank()', sort=[alt.SortField('avg_prev', order='ascending')]
).transform_filter('datum.rank == 1').mark_text(
    fontSize=20, fontWeight='bold', color='#00FF9F'
).encode(text='Region:N').properties(width=210, height=100, title="Lowest Risk Region")

# --- KPI: Fastest Growing (precomputed, embedded) ---
kpi_fastest = alt.Chart(growth_df).transform_filter(select_metric).transform_window(
    rank='rank()', sort=[alt.SortField('growth', order='descending')]
).transform_filter('datum.rank == 1').mark_text(
    fontSize=20, fontWeight='bold', color='#FFAC1C'
).encode(text='Region:N').properties(width=210, height=100, title="Fastest Growing Risk")

# --- KPI: Most Improved (smallest growth, could be negative) ---
kpi_improved = alt.Chart(growth_df).transform_filter(select_metric).transform_calculate(
    abs_growth='abs(datum.growth)'
).transform_window(
    rank='rank()', sort=[alt.SortField('abs_growth', order='ascending')]
).transform_filter('datum.rank == 1').mark_text(
    fontSize=20, fontWeight='bold', color='#B026FF'
).encode(text='Region:N').properties(width=210, height=100, title="Most Stable / Improved")

# --- KPI: Gender Gap (precomputed for all years & metrics) ---
gap_rows = []
for metric in ['BMI', 'BP', 'Diabetes']:
    for year in data['Year'].unique():
        g = gender_gap(data, metric, year)
        g['Metric'] = metric
        g['Year']   = year
        gap_rows.append(g)
gap_df = pd.concat(gap_rows)

kpi_gender_gap = alt.Chart(gap_df).transform_filter(select_year).transform_filter(
    select_metric
).transform_window(
    rank='rank()', sort=[alt.SortField('gap', order='descending')]
).transform_filter('datum.rank == 1').mark_text(
    fontSize=20, fontWeight='bold', color='#00D4FF'
).encode(text='Region:N').properties(width=210, height=100, title="Biggest Gender Gap")

kpi_row = alt.hconcat(
    kpi_highest, kpi_lowest, kpi_fastest, kpi_improved, kpi_gender_gap
).resolve_scale(color='independent')

# ── ROW 2: LINE CHART + GROUPED BAR CHART ────────────────────────────

# Line chart: health risk trends by region over time
line_base = alt.Chart(data).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(select_metric)

line_chart = line_base.mark_line(strokeWidth=2.5, point=True).encode(
    x=alt.X('Year:O', title='Year'),
    y=alt.Y('mean(Prevalence):Q', title='Mean Prevalence (%)', scale=alt.Scale(zero=False)),
    color=alt.Color('Region:N', legend=alt.Legend(title='Region')),
    tooltip=['Region:N', 'Year:O', alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Mean (%)')]
).properties(width=520, height=320, title="Health Risk Trends by Region Over Time")

# Grouped bar chart: metrics side-by-side per region for selected year
bar_grouped_base = alt.Chart(data).transform_filter(select_year).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence'])

bar_grouped = bar_grouped_base.mark_bar(opacity=0.85).encode(
    x=alt.X('Region:N', title='Region'),
    y=alt.Y('mean(Prevalence):Q', title='Mean Prevalence (%)', scale=alt.Scale(zero=False)),
    color=alt.Color('Metric:N', scale=alt.Scale(
        domain=['BMI', 'BP', 'Diabetes'],
        range=['#00FF9F', '#00D4FF', '#FF4D4D']
    )),
    xOffset=alt.XOffset('Metric:N'),
    tooltip=['Region:N', 'Metric:N', alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Mean (%)')]
).properties(width=520, height=320, title="Health Metrics by Region (Selected Year)")

row_2 = alt.hconcat(line_chart, bar_grouped).resolve_scale(color='independent')

# ── ROW 3: REGIONAL RISK SHARE + COMBO CHART ─────────────────────────

# Stacked bar: share of global prevalence by region over time
stacked_base = alt.Chart(data).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(select_metric)

stacked_risk_share = stacked_base.mark_bar().transform_aggregate(
    total_prev='sum(Prevalence)', groupby=['Year', 'Region']
).transform_joinaggregate(
    global_total='sum(total_prev)', groupby=['Year']
).transform_calculate(
    share='datum.total_prev / datum.global_total * 100'
).encode(
    x=alt.X('Year:O', title='Year'),
    y=alt.Y('share:Q', title='Prevalence Share (%)', stack='normalize',
            axis=alt.Axis(format='%')),
    color=alt.Color('Region:N'),
    tooltip=['Region:N', 'Year:O', alt.Tooltip('share:Q', format='.1f', title='Share (%)')]
).properties(width=520, height=320, title="Regional Risk Share of Global Prevalence")

# Combo chart: avg prevalence (line) + urbanisation (bars) by region for selected year
combo_bars = alt.Chart(data).transform_filter(select_year).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(
    select_metric
).mark_bar(opacity=0.6, color='#B026FF').encode(
    x=alt.X('Region:N', title='Region'),
    y=alt.Y('mean(Urban_Population):Q', title='Avg Urbanisation (%)'),
    tooltip=['Region:N', alt.Tooltip('mean(Urban_Population):Q', format='.1f', title='Urbanisation (%)')]
)

combo_line = alt.Chart(data).transform_filter(select_year).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(
    select_metric
).mark_line(color='#00FF9F', strokeWidth=3, point=alt.OverlayMarkDef(color='#00FF9F', size=60)).encode(
    x=alt.X('Region:N', title='Region'),
    y=alt.Y('mean(Prevalence):Q', title='Mean Prevalence (%)', scale=alt.Scale(zero=False)),
    tooltip=['Region:N', alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Prevalence (%)')]
)

combo_chart = alt.layer(combo_bars, combo_line).resolve_scale(
    y='independent'
).properties(width=520, height=320, title="Risk vs. Urbanisation by Region")

row_3 = alt.hconcat(stacked_risk_share, combo_chart).resolve_scale(color='independent')

# ── ASSEMBLY ──────────────────────────────────────────────────────────
page_regional = alt.vconcat(
    regional_title,
    kpi_row,
    row_2,
    row_3,
    spacing=50,
    center=True
).add_params(
    select_metric,
    select_year
)

page_regional = page_regional.configure_view(
    stroke=None
).configure_title(
    anchor='middle'
)

# Save raw html first
page_regional.save('page3_regional.html')
regional_json = page_regional.to_json()
print("Page 3 saved ✅")


# ── SAVE WITH NAV BAR ─────────────────────────────────────────────────
def save_dashboard(chart, filename, active_page):
    chart_json = chart.to_json()

    btn1 = 'active' if active_page == 'overview' else ''
    btn2 = 'active' if active_page == 'socio'    else ''
    btn3 = 'active' if active_page == 'regional' else ''

    html = f"""<!DOCTYPE html>
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
      text-decoration: none;
    }}
    .tab-btn:hover {{ color: white; border-color: #555; }}
    .tab-btn.active {{
      color: #00D4FF;
      border-color: #00D4FF;
      text-shadow: 0 0 8px rgba(0,212,255,0.6);
      box-shadow: inset 0 0 10px rgba(0,212,255,0.2);
    }}
    .sticky-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      background: #2b2b2b;
      padding-bottom: 10px;
    }}
    .filter-box {{ 
      background: #3d3d3d; 
      padding: 15px 25px; 
      border-radius: 12px; 
      border: 1px solid #555;
      margin-bottom: 0;
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
      width: fit-content;
    }}
    .vega-bind {{ color: white !important; font-size: 14px; margin-right: 20px; }}
    .vega-bind-name {{ font-weight: bold; color: #00D4FF; }}
  </style>
</head>
<body>

  <div class="sticky-bar">
    <div class="nav-bar">
      <a href="page1_overview.html"  class="tab-btn {btn1}">1. Overview</a>
      <a href="page2_socio.html"     class="tab-btn {btn2}">2. Socioeconomic</a>
      <a href="page3_regional.html"  class="tab-btn {btn3}">3. Regional Risk</a>
    </div>
    <div id="filters" class="filter-box"></div>
  </div>

  <div id="vis"></div>

  <script>
    vegaEmbed('#vis', {chart_json}, {{
      actions: false,
      bind: '#filters'
    }}).catch(console.error);
  </script>

</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{filename} saved ✅")


save_dashboard(page_regional, "page3_regional.html", "regional")