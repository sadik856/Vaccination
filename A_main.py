import datetime
import json
import numpy as np
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
from fake_useragent import UserAgent
from footer_utils import image, link, layout, footer


st.set_page_config(layout='wide',
                   initial_sidebar_state='collapsed',
                   page_title="Vaccination Slot")

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_mapping():
    df = pd.read_csv("district_mapping.csv")
    return df

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def filter_capacity(df, col, value):
    df_temp = deepcopy(df.loc[df[col] > value, :])
    return df_temp

@st.cache(allow_output_mutation=True)
def Pageviews():
    return []

mapping_df = load_mapping()

rename_mapping = {
    'date': 'Date',
    'available_capacity': 'Available Capacity',
    'state_name' : 'State',
    'district_name' : 'District',
    }

st.title('Vaccination Slot')
st.info('If you may not see an output! Please try after sometime ')

valid_states = list(np.unique(mapping_df["state_name"].values))

center_column_1, right_column_1 = st.beta_columns(2)

with center_column_1:
    state_inp = st.selectbox('Select State', [""] + valid_states)
    if state_inp != "":
        mapping_df = filter_column(mapping_df, "state_name", state_inp)

mapping_dict = pd.Series(mapping_df["district id"].values,
                         index = mapping_df["district name"].values).to_dict()
unique_districts = list(mapping_df["district name"].unique())
unique_districts.sort()
with right_column_1:
    dist_inp = st.selectbox('Select District', unique_districts)

DIST_ID = mapping_dict[dist_inp]

base = datetime.datetime.today()
date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
date_str = [x.strftime("%d-%m-%Y") for x in date_list]

temp_user_agent = UserAgent()
browser_header = {'User-Agent': temp_user_agent.random}

final_df = None
for INP_DATE in date_str:
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_ID, INP_DATE)
    response = requests.get(URL, headers=browser_header)
    if (response.ok) and ('centers' in json.loads(response.text)):
        resp_json = json.loads(response.text)['centers']
        if resp_json is not None:
            df = pd.DataFrame(resp_json)
            if len(df):
                df = df.explode("sessions")
                df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                df['date'] = df.sessions.apply(lambda x: x['date'])
                df = df[["date", "available_capacity",  "name", "state_name", "district_name"]]
                if final_df is not None:
                    final_df = pd.concat([final_df, df])
                else:
                    final_df = deepcopy(df)
        else:
            st.error("No rows in the data")
if (final_df is not None) and (len(final_df)):
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns=rename_mapping, inplace=True)

    right_column_2a = st.beta_columns(1)
    with right_column_2a:
        valid_capacity = ["Available"]
        cap_inp = st.selectbox('Select Availablilty', [""] + valid_capacity)
        if cap_inp != "":
            final_df = filter_capacity(final_df, "Available Capacity", 0)


    table = deepcopy(final_df)
    table.reset_index(inplace=True, drop=True)
    st.table(table)
else:
    st.error("please try after sometime")
pageviews=Pageviews()
pageviews.append('dummy')
pg_views = len(pageviews)
footer(pg_views)