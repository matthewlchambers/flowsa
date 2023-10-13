# BEA.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8

"""
Supporting functions for BEA data.

Generation of BEA Gross Output data and industry transcation data as FBA,
Source csv files for BEA data are documented
in scripts/write_BEA_Use_from_useeior.py
"""

import pandas as pd
from flowsa.location import US_FIPS
from flowsa.settings import input_paths
from flowsa.flowbyfunctions import assign_fips_location_system, aggregator

def bea_parse(*, source, year, **_):
    """
    Parse BEA data for GrossOutput, Make, and Use tables
    :param source:
    :param year:
    :return:
    """

    if 'Make' in source:
        filename = source.replace('_Make_', f'_Make_{year}_')
    elif 'Use' in source:
        filename = source.replace('_Use_', f'_Use_{year}_')
    else:
        filename = source

    df = pd.read_csv(input_paths.external_data % f"{filename}.csv")

    if 'BeforeRedef' in source:
        df = df.rename(columns={'Unnamed: 0': 'ActivityProducedBy'})
        # use "melt" fxn to convert colummns into rows
        df = df.melt(id_vars=["ActivityProducedBy"],
                     var_name="ActivityConsumedBy",
                     value_name="FlowAmount")
    elif '_Make_AfterRedef' in source:
        # strip whitespace
        for c in list(df.select_dtypes(include=['object']).columns):
            df[c] = df[c].apply(lambda x: x.strip())
        # drop rows of data
        df = df[df['Industry'] == df['Commodity']].reset_index(drop=True)
        # drop columns
        df = df.drop(columns=['Commodity', 'CommodityDescription'])
        # rename columns
        df = df.rename(columns={'Industry': 'ActivityProducedBy',
                                'IndustryDescription': 'Description',
                                'ProVal': 'FlowAmount',
                                'IOYear': 'Year'})
    elif 'GrossOutput' in source:
        df = df.rename(columns={'Unnamed: 0': 'ActivityProducedBy'})
        df = df.melt(id_vars=["ActivityProducedBy"],
                     var_name="Year",
                     value_name="FlowAmount")
        df = df[df['Year'] == year]

    df = df.reset_index(drop=True)

    # columns relevant to all BEA data
    df["SourceName"] = source
    df['Year'] = str(year)
    df['FlowName'] = f"USD{str(year)}"
    df["Class"] = "Money"
    df["FlowType"] = "TECHNOSPHERE_FLOW"
    df["Location"] = US_FIPS
    df = assign_fips_location_system(df, year)
    df['FlowAmount'] = df['FlowAmount']
    df["Unit"] = "Million USD"
    df['DataReliability'] = 5  # tmp
    df['DataCollection'] = 5  # tmp
    df['Description'] = filename

    return df
