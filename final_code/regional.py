import pandas as pd
import altair as alt
import squarify

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

# --- GLOBAL SELECTIONS ---
select_year = alt.selection_point(
    name="year_socio",
    fields=['Year'], 
    bind=alt.binding_range(min=1980, max=2016, step=1, name='Year: '), 
    value=2014
)

metric_radio_reg = alt.binding_radio(options=['BMI', 'BP', 'Diabetes'], name="Select Metric: ")
select_metric_reg = alt.selection_point(
    fields=['Metric'],  # ← matches the line chart fold name
    bind=metric_radio_reg,
    value='BMI',
    name="reg_metric"
)

# ── TITLE ─────────────────────────────────────────────────────────────
regional_title = alt.Chart(pd.DataFrame({'t': ["Regional Risk Analysis"]})).mark_text(
    align='center', fontSize=28, fontWeight='bold', color='#00D4FF'
).encode(text='t:N').properties(width=1100, height=50)

# ── MULTI-LINE KPI HELPER ─────────────────────────────────────────────
def finalize_kpi_multiline(chart, title_text, color_hex):
    return chart.properties(
        width=215, height=160,
        title=alt.TitleParams(text=title_text, fontSize=20, anchor='middle', color='white')
    ).mark_text(
        fontSize=15, 
        fontWeight='bold', 
        color=color_hex, 
        align='center',
        baseline='middle',
        lineBreak='\n'
    )

# ── KPI 1: Highest Risk ───────────────────────────────────────────────
highest_risk_kpi = finalize_kpi_multiline(
    alt.Chart(data).transform_filter(select_year).transform_fold(
        ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
    ).transform_filter(select_metric_reg).transform_aggregate(
        avg_prev='mean(Prevalence)', groupby=['Region', 'Metric']
    ).transform_window(
        rank='rank()', sort=[alt.SortField('avg_prev', order='descending')]
    ).transform_filter('datum.rank == 1').transform_calculate(
        display_text = "datum.Region + '\\n(' + format(datum.avg_prev, '.1f') + '%)'"
    ).encode(text='display_text:N'),
    "Highest Risk", '#FF4D4D'
)

# ── KPI 2: Lowest Risk ────────────────────────────────────────────────
lowest_risk_kpi = finalize_kpi_multiline(
    alt.Chart(data).transform_filter(select_year).transform_fold(
        ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
    ).transform_filter(select_metric_reg).transform_aggregate(
        avg_prev='mean(Prevalence)', groupby=['Region', 'Metric']
    ).transform_window(
        rank='rank()', sort=[alt.SortField('avg_prev', order='ascending')]
    ).transform_filter('datum.rank == 1').transform_calculate(
        display_text = "datum.Region + '\\n(' + format(datum.avg_prev, '.1f') + '%)'"
    ).encode(text='display_text:N'),
    "Lowest Risk", '#00FF9F'
)

# ── KPI 3: Fastest Growth ────────────────────────────────────────────
fastest_growing_kpi = finalize_kpi_multiline(
    alt.Chart(data).transform_fold(
        ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
    ).transform_filter(select_metric_reg).transform_aggregate(
        avg_prev='mean(Prevalence)', groupby=['Region', 'Year', 'Metric']
    ).transform_window(
        first_val='first_value(avg_prev)', last_val='last_value(avg_prev)',
        sort=[alt.SortField('Year', order='ascending')], groupby=['Region', 'Metric']
    ).transform_calculate(growth = "datum.last_val - datum.first_val").transform_aggregate(
        max_growth = "max(growth)", groupby=['Region', 'Metric']
    ).transform_window(
        rank='rank()', sort=[alt.SortField('max_growth', order='descending')]
    ).transform_filter('datum.rank == 1').transform_calculate(
        display_text = "datum.Region + '\\n(+' + format(datum.max_growth, '.1f') + 'pp)'"
    ).encode(text='display_text:N'),
    "Fastest Growth", '#B026FF'
)

# ── KPI 4: Largest Gender Gap ─────────────────────────────────────────
gender_gap_kpi = finalize_kpi_multiline(
    alt.Chart(data).transform_filter(select_year).transform_filter(
        alt.FieldOneOfPredicate(field='Gender', oneOf=['Men', 'Women'])
    ).transform_fold(['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']).transform_filter(select_metric_reg).transform_aggregate(
        avg_prev='mean(Prevalence)', groupby=['Region', 'Gender', 'Metric']
    ).transform_window(
        male_val='max(avg_prev)', female_val='min(avg_prev)', groupby=['Region', 'Metric']
    ).transform_calculate(gap = "abs(datum.male_val - datum.female_val)").transform_window(
        rank='rank()', sort=[alt.SortField('gap', order='descending')]
    ).transform_filter('datum.rank == 1').transform_calculate(
        display_text = "datum.Region + '\\n(' + format(datum.gap, '.1f') + 'pp Diff)'"
    ).encode(text='display_text:N'),
    "Largest Gender Gap", '#00D4FF'
)

# ── KPI 5: Most Stable ───────────────────────────────────────────────
most_improved_kpi = finalize_kpi_multiline(
    alt.Chart(data).transform_fold(
        ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence']
    ).transform_filter(select_metric_reg).transform_aggregate(
        avg_prev='mean(Prevalence)', groupby=['Region', 'Year', 'Metric']
    ).transform_window(
        first_val='first_value(avg_prev)', 
        last_val='last_value(avg_prev)',
        sort=[alt.SortField('Year', order='ascending')], 
        groupby=['Region', 'Metric']
    ).transform_calculate(
        growth = "datum.last_val - datum.first_val"
    ).transform_window(
        rank='row_number()', 
        sort=[
            alt.SortField('growth', order='ascending'),
            alt.SortField('Region', order='ascending') 
        ]
    ).transform_filter(
        'datum.rank == 1'
    ).transform_calculate(
        display_text = "datum.Region + '\\n(+' + format(datum.growth, '.1f') + 'pp)'"
    ).encode(
        text='display_text:N'
    ),
    "Most Stable", '#00D4FF'
)

# ── LINE CHART — Regional Risk Evolution ─────────────────────────────
regional_line_chart = alt.Chart(data).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric', 'Prevalence_line']
).transform_filter(
    select_metric_reg
).mark_line(
    point=True,
    interpolate='monotone',
    strokeWidth=3
).encode(
    x=alt.X(
        'Year:Q',
        title='Year',
        axis=alt.Axis(format='d', grid=False)
    ),
    y=alt.Y(
        'mean(Prevalence_line):Q',
        title='Mean Prevalence (%)',
        scale=alt.Scale(zero=False)
    ),
    color=alt.Color(
        'Region:N',
        scale=alt.Scale(scheme='tableau10'),
        legend=alt.Legend(title="Region")
    ),
    
    # 🔧 THIS LINE FIXES THE FILTER ISSUE
    detail='Metric:N',

    tooltip=[
        alt.Tooltip('Region:N', title='Region'),
        alt.Tooltip('Year:Q', format='d', title='Year'),
        alt.Tooltip('mean(Prevalence_line):Q', format='.1f', title='Avg Prevalence %')
    ]
).properties(
    width=1000,
    height=350,
    title=alt.TitleParams(
        text="Global Velocity: Regional Risk Evolution",
        anchor='middle'
    )
)

# ── GROUPED BAR — uses 'Metric_bar' and 'Prevalence_bar' ─────────────
region_grouped_bar = alt.Chart(data).transform_filter(
    select_year
).transform_fold(
    ['BMI', 'BP', 'Diabetes'], as_=['Metric_bar', 'Prevalence_bar']
).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
    x=alt.X('Region:N', title=None, axis=alt.Axis(labelAngle=-45, labelColor='white')),
    y=alt.Y('mean(Prevalence_bar):Q', title='Mean Prevalence (%)', stack=None),
    xOffset='Metric_bar:N',
    color=alt.Color('Metric_bar:N',
                    scale=alt.Scale(domain=['BMI', 'BP', 'Diabetes'],
                                    range=['#FF4D4D', '#00FF9F', '#B026FF']),
                    legend=alt.Legend(title="Health Indicator", orient='top')),
    tooltip=[
        'Region:N',
        'Metric_bar:N',
        alt.Tooltip('mean(Prevalence_bar):Q', format='.1f', title='Avg Prevalence %')
    ]
).properties(
    width=1000, height=400,
    title=alt.TitleParams(
        text="Regional Health Dominance Comparison",
        subtitle="Comparing the relative prevalence of BMI, Blood Pressure, and Diabetes",
        fontSize=22, anchor='middle', color='white'
    )
)

# ── ASSEMBLY ──────────────────────────────────────────────────────────

kpi_row = alt.hconcat(
    highest_risk_kpi, lowest_risk_kpi, fastest_growing_kpi, gender_gap_kpi, most_improved_kpi
).resolve_scale(color='independent')

page_regional = alt.vconcat(
    regional_title, 
    kpi_row,
    regional_line_chart,
    region_grouped_bar,
    spacing=60,
    center=True 
).add_params(
    select_year,
    select_metric_reg
).configure_view(stroke=None)

# --- DASHBOARD EXPORT LOGIC ---

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
    body {{ background-color: #2b2b2b; font-family: 'Segoe UI', sans-serif; color: white; display: flex; flex-direction: column; align-items: center; padding: 20px; }}
    .nav-bar {{ display: flex; gap: 15px; margin-bottom: 30px; background: #1a1a1a; padding: 10px 20px; border-radius: 8px; border: 1px solid #444; }}
    .tab-btn {{ background: transparent; color: #aaa; border: 2px solid transparent; padding: 10px 20px; font-size: 16px; font-weight: bold; border-radius: 5px; cursor: pointer; text-decoration: none; transition: 0.3s; }}
    .tab-btn.active {{ color: #00D4FF; border-color: #00D4FF; }}
    .filter-box {{ background: #3d3d3d; padding: 15px 25px; border-radius: 12px; border: 1px solid #555; margin-bottom: 30px; }}
    .vega-bind {{ color: white !important; font-size: 14px; margin-right: 20px; }}
    .vega-bind-name {{ font-weight: bold; color: #00D4FF; }}
  </style>
</head>
<body>
  <div class="nav-bar">
    <a href="page1_overview.html" class="tab-btn {btn1}">1. Overview</a>
    <a href="page2_socio.html" class="tab-btn {btn2}">2. Socioeconomic</a>
    <a href="page3_regional.html" class="tab-btn {btn3}">3. Regional Risk</a>
  </div>
  <div id="filters" class="filter-box"></div>
  <div id="vis"></div>
  <script>
    vegaEmbed('#vis', {chart_json}, {{ actions: false, bind: '#filters' }}).catch(console.error);
  </script>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{filename} saved successfully! ✅")

# Final Save Execution
save_dashboard(page_regional, "page3_regional.html", "regional")