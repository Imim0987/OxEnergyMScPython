"""
Functions, Classes and Modules Tutorial
This file demonstrates Python functions.

Learning objectives:
- Defining and using functions

Complete the script by filling in the missing code sections marked with <---.

@author: Tamunoimim
"""

# Import any necessary libraries
import math
import pandas as pd
import numpy as np
import os

# <--- Define a function to size a PV system based on building dimensions and panel specifications
def calculate_pv_size(building_length, building_width, roof_angle, panel_width, panel_length, panel_power): # <--- include parameters for building length, width, roof angle, panel width, panel height and panel power
    """
    building_width: float
       Building width is in meters
    building_length: float
       Building length is in meters
    roof_angle: float
       Roof angle is in degrees
    panel_width: float
       PV panel width is in mm
    panel_height: float
       PV panel height is in mm
    panel_power: float
       PV panel power rating is in watts

    This is a docstring. Use it to describe the function's purpose, parameters, and return values.
    """

    num_panels_length = building_length // (panel_length / 1000)  # <--- calculate number of panels that fit along the length of the building
    num_panels_width = (building_width / 2)/(math.cos(math.radians(roof_angle))) // (panel_width / 1000)  # <--- calculate number of panels that fit along the width of the building

    num_panels = int(num_panels_length * num_panels_width)  # <--- calculate total number of panels
    pv_capacity_kw = (num_panels * panel_power) / 1000  # <--- calculate total PV capacity in kW

    return pv_capacity_kw, num_panels # <--- return the total PV capacity in kW and number of panels

if __name__ == "__main__":
    # =============================================================================
    # This section is a common way to incorporate code that you want to run if the 
    # script is executed directly, but will be ignored if the script is 
    # imported as a module into another. 
    # 
    # It separates the executable part of the script from the part that defines
    # reusable components e.g. functions.
    # 
    # This is useful way of testing the code or providing examples of how to 
    # use the code.
    # =============================================================================
    holywell_house_dimensions = {
        "length": 16,  # in meters
        "width": 30,   # in meters
        "roof_angle": 22  # in degrees
    }

    panel_specs= {
        "length_mm": 10460,  # in mm
        "width_mm": 1690,   # in mm
        "power_w": 400  # in watts

      }
    pv_capacity_kw, num_panels = calculate_pv_size(
        building_length=holywell_house_dimensions["length"],
        building_width=holywell_house_dimensions["width"],
        roof_angle=holywell_house_dimensions["roof_angle"],
        panel_width=panel_specs["width_mm"],
        panel_length=panel_specs["length_mm"],  # in mm
        panel_power=panel_specs["power_w"]  # in watts
    )

    print(f'Number of PV panels: {num_panels}')
    print(f'Total PV capacity: {pv_capacity_kw} kW')
