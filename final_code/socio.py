import pandas as pd
import altair as alt

data = pd.read_pickle("final_code\clean_data.pkl")
alt.data_transformers.disable_max_rows()

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
    name="region_socio",  # ← add this
    fields=['Region'], 
    bind=alt.binding_select(options=region_options, labels=region_labels, name='Region: ')
)

select_year = alt.selection_point(
    name="year_socio",    # ← add this too
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
    select_region & select_year
).properties(width=250, height=100, title="Avg GDP per Capita")

kpi_urban = alt.Chart(data).mark_text(
    fontSize=40, fontWeight='bold', color='#B026FF', align='center'
).encode(
    text=alt.Text('mean(Urban_Population):Q', format='.1f')
).transform_filter(
    select_region & select_year
).properties(width=250, height=100, title=alt.TitleParams(text="Avg Urbanisation %", color='#FFFFFF', fontSize=14))

kpi_gender_risk = alt.Chart(data).transform_filter(
    select_region & select_year
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

urban_majority_kpi = alt.Chart(data).transform_filter(
    select_region & select_year
).transform_calculate(
    # 1. Check the "hats" (individual country status) FIRST
    # Note: Using Urban_Population to match your existing KPI column name
    is_urban_majority = "datum.Urban_Population > 50 ? 1 : 0"
).transform_aggregate(
    # 2. Now count them up
    count_majority = "sum(is_urban_majority)",
    total_count = "count()" 
).transform_calculate(
    # 3. Do the final math
    percentage_majority = "(datum.count_majority / datum.total_count) * 100",
    display_text = "'% of Countries >50% Urban: ' + format(datum.percentage_majority, '.0f') + '%'"
).mark_text(
    fontSize=22, 
    fontWeight='bold', 
    color='#00FF9F', 
    align='center'
).encode(
    text='display_text:N'
).properties(
    width=350, 
    height=100,
    title=alt.TitleParams(
        text="Urban Majority Indicator",
        color='white',
        fontSize=14
    )
)

risk_classification_kpi = alt.Chart(data).transform_filter(
    select_region & select_year
).transform_aggregate(
    # Step 1: Get global averages for the current selection to use as thresholds
    avg_gdp_global = 'mean(GDP)',
    avg_bmi_global = 'mean(BMI)',
).transform_calculate(
    # Step 2: Categorize each country
    # We use a nested ternary: (Condition) ? 'Result' : (Else Condition) ? 'Result' : 'Default'
    risk_cat = (
        "(datum.GDP > datum.avg_gdp_global && datum.BMI > datum.avg_bmi_global) ? 'Affluent Risk' : "
        "(datum.GDP <= datum.avg_gdp_global && datum.BMI > datum.avg_bmi_global) ? 'Emerging Risk' : "
        "(datum.BMI <= datum.avg_bmi_global) ? 'Low Risk' : 'Other'"
    )
).transform_aggregate(
    # Step 3: Find which category has the most countries (The Mode)
    count_per_cat = 'count()',
    groupby=['risk_cat']
).transform_window(
    # Step 4: Rank categories to find the "Dominant" one
    rank='rank()',
    sort=[alt.SortField('count_per_cat', order='descending')]
).transform_filter(
    'datum.rank == 1'
).transform_calculate(
    # Step 5: Final Formatting
    display_text = "'Dominant Pattern: ' + datum.risk_cat"
).mark_text(
    fontSize=22, 
    fontWeight='bold', 
    color='#FF4D4D', # Cyberpunk Red for "Risk"
    align='center'
).encode(
    text='display_text:N'
).properties(
    width=350, 
    height=100,
    title=alt.TitleParams(
        text="Development vs Risk Classification",
        subtitle="Identifying Structural Health Trends",
        color='white'
    )
)

base = alt.Chart(data).transform_filter(
    select_region & select_year
).transform_filter(
    alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
).encode(
    x=alt.X('IncomeGroup:N', 
            title='Income Group', 
            sort=['High income', 'Upper middle income', 'Lower middle income', 'Low income']),
    color=alt.Color('Gender:N', scale=gender_scale),
    xOffset=alt.XOffset('Gender:N')
)

# 1. The Bars: Now with a "Swiss Army Knife" of a tooltip
bars = base.mark_bar(size=30, opacity=0.8).encode(
    y=alt.Y('mean(Prevalence):Q', title='Mean Prevalence (%)', scale=alt.Scale(zero=False)),
    tooltip=[
        'IncomeGroup:N', 
        'Gender:N', 
        alt.Tooltip('mean(Prevalence):Q', format='.1f', title='Mean (%)'),
        # Adding the quantiles here!
        alt.Tooltip('q1(Prevalence):Q', format='.1f', title='Q1 (25th Perc)'),
        alt.Tooltip('q3(Prevalence):Q', format='.1f', title='Q3 (75th Perc)'),
        # Why not add the Standard Deviation too? Just for the flex.
        alt.Tooltip('stdev(Prevalence):Q', format='.1f', title='Std. Deviation')
    ]
)

# 2. The Error Bars (Mean +/- Standard Deviation)
# These stay the same, looking sharp and professional.
error_bars = base.mark_errorbar(extent='stdev', color='black').encode(
    y=alt.Y('Prevalence:Q')
)

# Combine them into the final masterpiece
bar_socio = (bars + error_bars).properties(
    width=750, 
    height=350, 
    title="Health Distribution: Mean bars with Q1/Q3 in Tooltip"
)

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
kpi_row = alt.hconcat(
    kpi_gdp, kpi_urban, kpi_gender_risk
).resolve_scale(color='independent')\

kpi_row_2 = alt.hconcat(
    urban_majority_kpi, risk_classification_kpi
).resolve_scale(color='independent')

page_socio = alt.vconcat(
    socio_title,
    kpi_row, 
    kpi_row_2,
    bar_socio,
    final_heatmap
).add_params(
    select_region, select_year  # ← ONLY page 2 signals here
).configure_view(stroke=None).configure_concat(spacing=40)

# ── SAVE AS SEPARATE HTML ─────────────────────────────────────────────
page_socio.save('page2_socio.html')
socio_json = page_socio.to_json()
print("Page 2 saved ✅")


def save_dashboard(chart, filename, active_page):
    chart_json = chart.to_json()
    
    # Set which button is active based on current page
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