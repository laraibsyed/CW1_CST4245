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


page_overview = alt.vconcat(
    title_header, kpi_row, middle_row, bottom_floor
).add_params(select_region, select_year).configure_view(stroke=None).configure_concat(spacing=40)

overview_json = page_overview.to_json()

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


save_dashboard(page_overview, "page1_overview.html", "overview")