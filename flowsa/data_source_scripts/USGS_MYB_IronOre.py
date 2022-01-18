# USGS_MYB_IronOre.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8

"""
Projects
/
FLOWSA
/

FLOWSA-314

Import USGS Mineral Yearbook data

Description

SourceName: USGS_MYB_Iron_Ore
https://www.usgs.gov/centers/nmic/iron-ore-statistics-and-information

Minerals Yearbook, xls file, tab T1: SALIENT IRON ORE STATISTICS
data for:

Iron Ore, US production

Years = 2014+
"""
import io
import pandas as pd
from flowsa.flowbyfunctions import assign_fips_location_system
from flowsa.data_source_scripts.USGS_MYB_Common import *
SPAN_YEARS = "2014-2018"


def usgs_iron_ore_url_helper(*, build_url, **_):
    """
     This helper function uses the "build_url" input from flowbyactivity.py,
    which is a base url for data imports that requires parts of the url text
    string to be replaced with info specific to the data year. This function
    does not parse the data, only modifies the urls from which data is
    obtained.
    :param build_url: string, base url
    :return: list, urls to call, concat, parse, format into Flow-By-Activity
        format
    """
    url = build_url
    return [url]


def usgs_iron_ore_call(*, resp, year, **_):
    """
    Convert response for calling url to pandas dataframe, begin parsing
    df into FBA format
    :param resp: df, response from url call
    :param year: year
    :return: pandas dataframe of original source data
    """
    df_raw_data = pd.io.excel.read_excel(io.BytesIO(resp.content),
                                         sheet_name='T1 ')
    df_data = pd.DataFrame(df_raw_data.loc[7:25]).reindex()
    df_data = df_data.reset_index()
    del df_data["index"]

    if len(df_data. columns) == 12:
        df_data.columns = ["Production", "Units", "space_1", "year_1",
                           "space_2", "year_2", "space_3", "year_3",
                           "space_4", "year_4", "space_5", "year_5"]
    col_to_use = ["Production", "Units"]
    col_to_use.append(usgs_myb_year(SPAN_YEARS, year))
    for col in df_data.columns:
        if col not in col_to_use:
            del df_data[col]

    return df_data


def usgs_iron_ore_parse(*, df_list, source, year, **_):
    """
    Combine, parse, and format the provided dataframes
    :param df_list: list of dataframes to concat and format
    :param source: source
    :param year: year
    :return: df, parsed and partially formatted to flowbyactivity
        specifications
    """
    data = {}
    name = usgs_myb_name(source)
    des = name
    row_to_use = ["Gross weight", "Quantity"]
    dataframe = pd.DataFrame()
    for df in df_list:
        for index, row in df.iterrows():

            if df.iloc[index]["Production"].strip() == "Production:":
                product = "production"
            elif df.iloc[index]["Production"].strip() == "Exports:":
                product = "exports"
            elif df.iloc[index]["Production"].strip() == \
                    "Imports for consumption:":
                product = "imports"

            if df.iloc[index]["Production"].strip() in row_to_use:
                data = usgs_myb_static_varaibles()
                data["SourceName"] = source
                data["Year"] = str(year)
                data["Unit"] = "Thousand Metric Tons"
                data['FlowName'] = "Iron Ore " + product
                data["Description"] = "Iron Ore"
                data["ActivityProducedBy"] = "Iron Ore"
                col_name = usgs_myb_year(SPAN_YEARS, year)
                if str(df.iloc[index][col_name]) == "--":
                    data["FlowAmount"] = str(0)
                else:
                    data["FlowAmount"] = str(df.iloc[index][col_name])
                dataframe = dataframe.append(data, ignore_index=True)
                dataframe = assign_fips_location_system(
                    dataframe, str(year))
    return dataframe
