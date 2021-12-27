# generate_data_visualization.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8

"""
Generate plots to explore Flow-By-Sector model outputs
"""
import flowsa

sectors = ['111']
sector_length_display = 6


# Produce facet graph of resources associated with cropland sectors
plottype = 'facet_graph'
method_dict = {'Water Withdrawal 2015': 'Water_national_2015_m1',
               'Land Use 2012': 'Land_national_2012',
               'Employment 2017': 'Employment_national_2017'}


fig1 = flowsa.generateFBSplot(method_dict, plottype,
                              sector_length_display=sector_length_display,
                              sectors_to_include=sectors,
                              plot_title='Direct Resource Use for Cropland'
                              )

# Compare the results between water method 1 and method 2
plottype = 'method_comparison'
method_dict = {'Water Withdrawal M1 2015': 'Water_national_2015_m1',
               'Water Withdrawal M2 2015': 'Water_national_2015_m2'}

fig2 = flowsa.generateFBSplot(method_dict, plottype,
                              sector_length_display=sector_length_display,
                              sectors_to_include=sectors,
                              plot_title='Comparison of National Water '
                                         'Withdrawals Method 1 and '
                                         'Method 2 for Cropland Subset'
                              )