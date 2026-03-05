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

region_options = [None] + sorted(data['Region'].dropna().unique().tolist())
region_labels = ['All'] + sorted(data['Region'].dropna().unique().tolist())

select_region = alt.selection_point(
    name="region_socio",
    fields=['Region'], 
    bind=alt.binding_select(options=region_options, labels=region_labels, name='Region: ')
)

select_year = alt.selection_point(
    name="year_socio",
    fields=['Year'], 
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '), 
    value=2014
)

# ── TITLE ─────────────────────────────────────────────────────────────
socio_title = alt.Chart(pd.DataFrame({'t': ["Socioeconomic Risk Analysis"]})).mark_text(
    align='center', fontSize=28, fontWeight='bold', color='#00D4FF'
).encode(text='t:N').properties(width=1100, height=50)

# ── ROW 1: KPI TILES ──────────────────────────────────────────────────
kpi_base = alt.Chart(data).transform_filter(select_region & select_year)

kpi_gdp = kpi_base.mark_text(fontSize=35, fontWeight='bold', color='#00FF9F').encode(
    text=alt.Text('mean(GDP):Q', format='$,.0f')
).properties(width=200, height=100, title="Avg GDP per Capita")

kpi_urban = kpi_base.mark_text(fontSize=35, fontWeight='bold', color='#B026FF').encode(
    text=alt.Text('mean(Urban_Population):Q', format='.1f')
).properties(width=200, height=100, title="Avg Urbanisation %")

kpi_gender_risk = kpi_base.transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_aggregate(
    avg_bmi='mean(BMI)', avg_bp='mean(BP)', avg_diabetes='mean(Diabetes)', groupby=['Gender']
).transform_calculate(
    total_risk="datum.avg_bmi + datum.avg_bp + datum.avg_diabetes"
).transform_window(
    rank='rank()', sort=[alt.SortField('total_risk', order='descending')]
).transform_filter('datum.rank == 1').mark_text(fontSize=28, fontWeight='bold').encode(
    text='Gender:N', color=alt.Color('Gender:N', scale=gender_scale, legend=None)
).properties(width=200, height=100, title="Highest Overall Risk")

urban_majority_kpi = kpi_base.transform_calculate(
    is_urban_majority = "datum.Urban_Population > 50 ? 1 : 0"
).transform_aggregate(
    count_majority = "sum(is_urban_majority)", total_count = "count()" 
).transform_calculate(
    percentage_majority = "(datum.count_majority / datum.total_count) * 100",
    display_text = "format(datum.percentage_majority, '.0f') + '%'"
).mark_text(fontSize=35, fontWeight='bold', color='#00FF9F').encode(
    text='display_text:N'
).properties(width=200, height=100, title="Countries >50% Urban")

risk_classification_kpi = kpi_base.transform_window(
    avg_gdp_global = 'mean(GDP)', avg_bmi_global = 'mean(BMI)', frame=[None, None]
).transform_calculate(
    risk_cat = (
        "(datum.GDP > datum.avg_gdp_global && datum.BMI > datum.avg_bmi_global) ? 'Affluent Risk' : "
        "(datum.GDP <= datum.avg_gdp_global && datum.BMI > datum.avg_bmi_global) ? 'Emerging Risk' : "
        "(datum.GDP > datum.avg_gdp_global && datum.BMI <= datum.avg_bmi_global) ? 'Resilient Wealth' : 'Developing Health'"
    )
).transform_aggregate(
    count_per_cat = 'count()', groupby=['risk_cat']
).transform_window(
    rank='rank()', sort=[alt.SortField('count_per_cat', order='descending')]
).transform_filter('datum.rank == 1').transform_calculate(
    status_color = (
        "datum.risk_cat == 'Emerging Risk' ? '#FF4D4D' : "
        "datum.risk_cat == 'Affluent Risk' ? '#FFAC1C' : "
        "datum.risk_cat == 'Resilient Wealth' ? '#00FF9F' : '#00D4FF'"
    )
).mark_text(fontSize=20, fontWeight='bold').encode(
    text='risk_cat:N', color=alt.Color('status_color:N', scale=None)
).properties(width=220, height=100, title="Dominant Risk Pattern")

kpi_row = alt.hconcat(
    kpi_gdp, kpi_urban, kpi_gender_risk, urban_majority_kpi, risk_classification_kpi
).resolve_scale(color='independent')

# ── ROW 2: BAR CHART & HEATMAP ────────────────────────────────────────
base_bar = alt.Chart(data).transform_filter(select_region & select_year).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence'])

bar_socio = alt.layer(
    base_bar.mark_bar(size=30, opacity=0.8).encode(
        x=alt.X('IncomeGroup:N', sort=['High income', 'Upper middle income', 'Lower middle income', 'Low income'], title="Income Group"),
        y=alt.Y('mean(Prevalence):Q', title='Mean Prevalence (%)', scale=alt.Scale(zero=False)),
        color=alt.Color('Gender:N', scale=gender_scale),
        xOffset=alt.XOffset('Gender:N'),
        tooltip=[
            'IncomeGroup:N', 'Gender:N', 
            alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Mean (%)'),
            alt.Tooltip('q1(Prevalence):Q', format='.1f', title='Q1'),
            alt.Tooltip('q3(Prevalence):Q', format='.1f', title='Q3')
        ]
    ),
    base_bar.mark_errorbar(extent='stdev', color='white').encode(
        x=alt.X('IncomeGroup:N', sort=['High income', 'Upper middle income', 'Lower middle income', 'Low income']),
        y=alt.Y('Prevalence:Q'),
        xOffset=alt.XOffset('Gender:N')
    )
).properties(width=550, height=300, title="Prevalence by Income & Gender")

corr_cols = ['BMI', 'BP', 'Diabetes', 'GDP', 'Urban_Population']
corr_matrix = data[corr_cols].corr().reset_index().melt(id_vars='index')
corr_matrix.columns = ['Var1', 'Var2', 'Correlation']

heatmap = alt.Chart(corr_matrix).mark_rect().encode(
    x=alt.X('Var1:N', title=None), y=alt.Y('Var2:N', title=None),
    color=alt.Color('Correlation:Q', scale=alt.Scale(scheme='viridis', domain=[-1, 1])),
    tooltip=[alt.Tooltip('Var1:N'), alt.Tooltip('Var2:N'), alt.Tooltip('Correlation:Q', format='.2f')]
).properties(width=350, height=300, title="Variable Correlations")

row_2 = alt.hconcat(bar_socio, heatmap + heatmap.mark_text().encode(
    text=alt.Text('Correlation:Q', format='.2f'),
    color=alt.condition(alt.datum.Correlation > 0.5, alt.value('black'), alt.value('white'))
)).resolve_scale(color='independent')

# ── ROW 3: SCATTER & TREND ────────────────────────────────────────────
metric_dropdown = alt.binding_select(options=['BMI', 'BP', 'Diabetes'], name='Scatter Metric: ')
select_metric = alt.selection_point(fields=['Metric'], bind=metric_dropdown, value='BMI', name="metric_selector")

scatter = alt.Chart(data).transform_filter(select_region & select_year).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
).transform_filter(select_metric).mark_circle(size=80, opacity=0.7).encode(
    x=alt.X('GDP:Q', title='GDP per Capita ($)', scale=alt.Scale(type='log')),
    y=alt.Y('Prevalence:Q', title='Prevalence (%)', scale=alt.Scale(zero=False)),
    color='Region:N', tooltip=['Country:N', 'GDP:Q', 'Prevalence:Q']
).properties(width=450, height=350, title="GDP vs. Prevalence Gradient")

metric_radio = alt.binding_radio(options=['BMI', 'BP', 'Diabetes'], name="Trend Metric: ")
select_metric_trend = alt.selection_point(fields=['Metric'], bind=metric_radio, value='BMI', name="metric_trend")

trend_base = alt.Chart(data).transform_filter(select_region).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
).transform_filter(select_metric_trend).encode(x=alt.X('Year:O', title='Year'))

trend_analysis = alt.layer(
    trend_base.mark_line(color='#00FF9F', strokeWidth=3).encode(y=alt.Y('mean(GDP):Q', title='Avg GDP ($)')),
    trend_base.mark_line(color='#FF4D4D', strokeWidth=3).encode(y=alt.Y('mean(Prevalence):Q', title='Prevalence (%)'))
).resolve_scale(y='independent').add_params(select_metric_trend).properties(
    width=450, height=350, title="Economic vs. Health Trends"
)

row_3 = alt.hconcat(scatter.add_params(select_metric), trend_analysis).resolve_scale(color='independent')

# ── ASSEMBLY ──────────────────────────────────────────────────────────
# Note: Based on your traceback, 'center' is a direct parameter of VConcatChart
page_socio = alt.vconcat(
    socio_title, 
    kpi_row, 
    row_2, 
    row_3,
    spacing=50,
    center=True # Moving center here instead of configure_concat
).add_params(
    select_region, 
    select_year
)

# Apply global configurations (Keeping it minimal to avoid schema conflicts)
page_socio = page_socio.configure_view(
    stroke=None
).configure_title(
    anchor='middle'
)

# Save the dashboard
page_socio.save('page2_socio.html')
socio_json = page_socio.to_json()
print("Page 2 saved ✅")


def save_dashboard(chart, filename, active_page):
    chart_json = chart.to_json()
    
    btn1 = 'active' if active_page == 'overview' else ''
    btn2 = 'active' if active_page == 'socio' else ''
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
    <a href="page1_overview.html" class="tab-btn {btn1}">1. Overview</a>
    <a href="page2_socio.html"    class="tab-btn {btn2}">2. Socioeconomic</a>
    <a href="page3_regional.html" class="tab-btn {btn3}">3. Regional Risk</a>
  </div>

  <div id="filters" class="filter-box"></div>
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


save_dashboard(page_socio, "page2_socio.html", "socio")