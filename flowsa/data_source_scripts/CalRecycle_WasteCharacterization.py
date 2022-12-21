# CalRecycle_WasteCharacterization.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8

"""
2014 California Commercial by sector
The original data came from
https://www2.calrecycle.ca.gov/WasteCharacterization/PubExtracts/2014/GenSummary.pdf
The data  was manually scraped so no R/python code is available to replicate.
Last updated:
"""

import pandas as pd
import numpy as np
from flowsa.flowbyfunctions import assign_fips_location_system, \
    load_fba_w_standardized_units, \
    aggregate_and_subset_for_target_sectors
from flowsa.settings import externaldatapath
from flowsa.sectormapping import get_fba_allocation_subset, \
    add_sectors_to_flowbyactivity
from flowsa.dataclean import replace_strings_with_NoneType, standardize_units


def produced_by(entry):
    """
    Modify source activity names to clarify data meaning
    :param entry: str, original source name
    :return: str, modified activity name
    """
    if "ArtsEntRec" in entry:
        return "Arts Entertainment Recreation"
    if "DurableWholesaleTrucking" in entry:
        return "Durable Wholesale Trucking"
    if "Education" in entry:
        return "Education"
    if "ElectronicEquipment" in entry:
        return "Electronic Equipment"
    if "FoodBeverageStores" in entry:
        return "Food Beverage Stores"
    if "FoodNondurableWholesale" in entry:
        return "Food Nondurable Wholesale"
    if "HotelLodging" in entry:
        return "Hotel Lodging"
    if "MedicalHealth" in entry:
        return "Medical Health"
    if "Multifamily" in entry:
        return "Multifamily"
    if "NotElsewhereClassified" in entry:
        return "Not Elsewhere Classified"
    if "OtherManufacturing" in entry:
        return "Other Manufacturing"
    if "OtherRetailTrade" in entry:
        return "Other Retail Trade"
    if "PublicAdministration" in entry:
        return "Public Administration"
    if "Restaurants" in entry:
        return "Restaurants"
    if "ServicesManagementAdminSupportSocial" in entry:
        return "Services Management Administration Support Social"
    if "ServicesProfessionalTechFinancial" in entry:
        return "Services Professional Technical Financial"
    if "ServicesRepairPersonal" in entry:
        return "Services Repair Personal"


def calR_parse(*, year, **_):
    """
    Combine, parse, and format the provided dataframes
    :param dataframe_list: list of dataframes to concat and format
    :param args: dictionary, used to run flowbyactivity.py
        ('year' and 'source')
    :return: df, parsed and partially formatted to
        flowbyactivity specifications
    """
    data = {}
    output = pd.DataFrame()

    data["Class"] = "Other"
    data['FlowType'] = "WASTE_FLOW"
    data["Location"] = "06000"
    # data["Compartment"] = "ground"
    data["SourceName"] = "CalRecycle_WasteCharacterization"
    data["Year"] = year
    data['DataReliability'] = 5  # tmp
    data['DataCollection'] = 5  # tmp

    for entry in externaldatapath.iterdir():
        if entry.is_file():
            if ("California_Commercial_bySector_2014" in entry.name and 
                    "Map" not in entry.name):
                data["ActivityProducedBy"] = produced_by(entry.name)
                dataframe = pd.read_csv(entry, header=0, dtype=str)
                for col in dataframe.columns:
                    if "Percent" in str(col):
                        del dataframe[col]

                for index, row in dataframe.iterrows():
                    data['FlowName'] = row["Material"]
                    for field, value in row[1:].items():
                        col_string = field.split()
                        data["Unit"] = col_string[1].lower()
                        data['Description'] = col_string[0]
                        if value != "-":
                            data["FlowAmount"] = int(value)
                            output = pd.concat([output,
                                                pd.DataFrame(data, index=[0])],
                                               ignore_index=True)
    output = assign_fips_location_system(output, year)
    return output


def keep_generated_quantity(fba, **_):
    """
    Function to clean CalRecycles FBA to remove quantities not
    assigned as Generated
    :param fba: df, FBA format
    :return: df, modified CalRecycles FBA
    """
    fba = fba[fba['Description'] == 'Generated'].reset_index(drop=True)
    # if no mapping performed, still update units
    if 'tons' in fba['Unit'].values:
        fba = standardize_units(fba)
    return fba


def load_and_clean_employment_data_for_cnhw(fbs, year, method,
                                            geographic_level='state'):
    from flowsa.data_source_scripts.BLS_QCEW import \
        bls_clean_allocation_fba_w_sec
    bls = load_fba_w_standardized_units(datasource='BLS_QCEW',
                                        year=year,
                                        flowclass='Employment',
                                        geographic_level=geographic_level)
    bls = add_sectors_to_flowbyactivity(bls)
    # estimate suppressed employment data
    bls = bls_clean_allocation_fba_w_sec(bls, method=method)

    # Subset BLS dataset
    sector_list = list(filter(None, fbs['SectorProducedBy'].unique()))
    bls = get_fba_allocation_subset(bls, 'BLS_QCEW', sector_list)
    bls = bls.rename(columns={'FlowAmount': 'Employees'})
    bls = bls[['Employees', 'Location', 'Year', 'SectorProducedBy']]
    return bls


def apply_tons_per_employee_per_year_to_states(fbs, method, **_):
    """
    Calculates tons per employee per year based on BLS_QCEW employees
    by sector and applies that quantity to employees in all states
    clean_fbs_df_fxn
    """
    # load bls employment data for the year of CalRecycle data
    bls = load_and_clean_employment_data_for_cnhw(
        fbs, fbs['Year'].unique()[0], method)
    # Calculate tons per employee per year per material and sector in CA
    bls_CA = bls[bls['Location'] == '06000']  # California
    # aggregate all employment prior to generating tpepy
    bls_CA = (bls_CA.groupby(['Location', 'Year', 'SectorProducedBy'])
              .agg({'Employees': 'sum'})
              .reset_index())
    tpepy = fbs.merge(bls_CA, how='inner')
    tpepy['TPEPY'] = np.divide(tpepy['FlowAmount'], tpepy['Employees'],
                               out=np.zeros_like(tpepy['Employees']),
                               where=tpepy['Employees'] != 0)
    tpepy = tpepy.drop(columns=['Employees', 'FlowAmount', 'Location', 'Year'])

    # Apply TPEPY back to all employees in all states for year identified in
    # method, overwrite geoscale based on target geoscale identified in method
    bls2 = load_and_clean_employment_data_for_cnhw(
        fbs, _.get('v')['year'], method, method.get('target_geoscale'))
    national_waste = tpepy.merge(bls2, how='left')
    national_waste['Year'] = _.get('v')['year']
    national_waste['FlowAmount'] = \
        national_waste['Employees'] * national_waste['TPEPY']
    national_waste = national_waste.drop(columns=['TPEPY', 'Employees'])

    df = aggregate_and_subset_for_target_sectors(national_waste, method)
    df = replace_strings_with_NoneType(df)

    return df
