import pandas as pd
import altair as alt
import numpy as np
from datetime import date
from vega_datasets import data
import math

alt.data_transformers.enable('default', max_rows=None)
alt.renderers.enable('altair_viewer')
#Data Loading
uni_df = pd.read_csv("universal-map-covid.csv")
deliv_df = pd.read_csv('daily_change_in_seated_restaurant_diners.csv', parse_dates=['Date'])
cov_hist_df = pd.read_csv("daily-covid-hist.csv", parse_dates=['date'])

################# RUNNING THIS CODE BLOCK MORE THAN ONCE WILL BREAK IF YOU DON'T RUN THE ON ABOVE IT FIRST ######################################

#Cleaning Step for Historical
oldest_df = cov_hist_df.replace('suppressed', 0)
older_df = oldest_df.replace(',','', regex=True)
older_df["cases_per_100K_7_day_count_change"] = pd.to_numeric(older_df["cases_per_100K_7_day_count_change"])
cov_hist_df["cases_per_100K_7_day_count_change"] = older_df["cases_per_100K_7_day_count_change"].values
cov_hist_df.rename(columns = {'fips_code':'county_fips'}, inplace = True)

#Fixing Hist_DF
county_and_fips = uni_df[["county_fips","county"]].copy()

cov_hist_df = cov_hist_df.merge(county_and_fips, on='county_fips', how="left")

cov_hist_df.loc[cov_hist_df['county'] == 'Hays County']

#Kaleb's Attempt
cov_src = pd.read_csv("universal-map-covid.csv")

counties = alt.topo_feature(data.us_10m.url, 'counties')
states = alt.topo_feature(data.us_10m.url, 'states')

highlight = alt.selection_single(on='mouseover', fields=['id'], empty='none')

selector = alt.selection_single(fields=['county'])

#Geographic Map
plot = alt.Chart(counties).mark_geoshape().encode(
    color=alt.condition(highlight, alt.value('gold'), 'covid_cases_per_100k:Q'),
    tooltip=['county:N', alt.Tooltip('covid_cases_per_100k:Q', title="covid rate per 100k")]
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(cov_src, key='county_fips', fields=['county','covid_cases_per_100k'])
).add_selection(highlight).project(
    type='albersUsa'
).properties(
    width=900,
    height=600
).add_selection(selector)
outline = alt.Chart(states).mark_geoshape(stroke='blue', fillOpacity=0).project(
    type='albersUsa'
).properties(
    width=700,
    height=400,
    title="U.S. Covid Rates (per 100k) by County"
)

#Bar Chart at bottom

#List of all counties for selector
#county_selectable = uni_df["county"].values.tolist()

#County Selector
#county_dropdown = alt.binding_select(options=county_selectable, name='Select County ')
#county_selection = alt.selection_single(fields=['county'], bind=county_dropdown)

scale_last = deliv_df['Date'][len(deliv_df)-1]
scale_first = deliv_df['Date'][len(deliv_df)-90]

bar = alt.Chart(cov_hist_df).mark_bar().encode(
    x=alt.X('date', title="Date", scale=alt.Scale(
            domain=(scale_first, scale_last),
            clamp=True
        )),
    y=alt.Y('cases_per_100K_7_day_count_change:Q', title="Cases Per 100k"),
    color = alt.value("#2916D5")
).transform_filter(
    selector
)
deliv_df['rolling_mean'] = deliv_df['Percent Change'].rolling(7).mean()
chart = alt.Chart(deliv_df).mark_line().encode(
    alt.X('Date',
          scale=alt.Scale(
            domain=(scale_first, scale_last),
            clamp=True
        )),
    y=alt.Y('rolling_mean', title = "7-day Rolling Mean of Percent Change of In-Restaurant Diners"),
    color = alt.value("#FF8400")
)


#Rolling Mean Line to compensate for missing data
#TODO FIX
'''
line = alt.Chart(cov_hist_df.head(20000)).mark_line(color='yellow').transform_window(
    rolling_mean = 'mean(cases_per_100K_7_day_count_change)',
    frame=[-9,0]
).encode(
    x='date:O',
    y='rolling_mean:Q',
    color = 'county'
).add_selection(
    county_selection
).transform_filter(
    county_selection
)
'''


geog_map = alt.layer(plot,outline)
personal = alt.layer(bar,chart).properties(
    width=800,
    height=400,
    title="Covid Infection Rates for Selected County and Percent Change of In-Restaurant Diners for U.S."
).resolve_scale(y='independent').interactive()
dashboard = alt.vconcat(geog_map, personal)

dashboard.save("dashboard.html")
