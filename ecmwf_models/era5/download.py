# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2019,TU Wien
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Module to download ERA5 from terminal in netcdf and grib format.
'''

from ecmwf_models.utils import *
import argparse
import sys
import os
from datetime import datetime, timedelta, time
import shutil
import cdsapi
import calendar


def default_variables():
    'These variables are being downloaded, when None are passed by the user'
    lut = load_var_table(name='ERA5')
    defaults = lut.loc[lut['default'] == 1]['dl_name'].values
    return defaults.tolist()


def download_era5(c, years, months, days, h_steps, variables, target, grb=False,
                  dry_run=False):
    '''
    Download era5 reanalysis data for single levels of a defined time span

    Parameters
    ----------
    c : cdsapi.Client
        Client to pass the request to
    years : list
        Years for which data is downloaded ,e.g. [2017, 2018]
    months : list
        Months for which data is downloaded, e.g. [4, 8, 12]
    days : list
        Days for which data is downloaded (range(31)=All days) e.g. [10, 20, 31]
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    variables : list, optional (default: None)
        List of variables to pass to the client, if None are passed, the default
        variables will be downloaded.
    target : str
        File name, where the data is stored.
    geb : bool, optional (default: False)
        Download data in grib format
    dry_run: bool, optional (default: False)
        Do not download anything, this is just used for testing the functionality

    Returns
    ---------
    success : bool
        Return True after downloading finished
    '''

    if not dry_run:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'grib' if grb else 'netcdf',
                'variable': variables,
                'year': [str(y) for y in years],
                'month': [str(m).zfill(2) for m in months],
                'day': [str(d).zfill(2) for d in days],
                'time': [time(h, 0).strftime('%H:%M') for h in h_steps]
            },
            target)

    return True


def download_and_move(target_path, startdate, enddate, variables=None,
                      keep_original=False, h_steps=[0, 6, 12, 18],
                      grb=False, dry_run=False):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 day increments between start and end date.

    The files are then extracted into separate grib files per parameter and stored
    in yearly folders under the target_path.

    Parameters
    ----------
    target_path : str
        Path where the files are stored to
    startdate: datetime
        first date to download
    enddate: datetime
        last date to download
    variables : list, optional (default: None)
        Name of variables to download
    keep_original: bool
        keep the original downloaded data
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    grb: bool, optional (default: False)
        Download data as grib files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    """

    if variables is None:
        variables = default_variables()
    else:
        # find the dl_names
        variables = lookup(name='ERA5', variables=variables)
        variables = variables['dl_name'].values.tolist()

    curr_start = startdate

    if dry_run:
        warnings.warn('Dry run does not create connection to CDS')
        c = None
    else:
        c = cdsapi.Client()

    while curr_start <= enddate:
        sy, sm, sd = curr_start.year, curr_start.month, curr_start.day
        sm_days = calendar.monthrange(sy, sm)[1]  # days in the current month
        y, m = sy, sm

        if (enddate.year == y) and (enddate.month == m):
            d = enddate.day
        else:
            d = sm_days

        curr_end = datetime(y, m, d)

        fname = '{start}_{end}.{ext}'.format(start=curr_start.strftime("%Y%m%d"),
                                             end=curr_end.strftime("%Y%m%d"),
                                             ext='grb' if grb else 'nc')

        downloaded_data_path = os.path.join(target_path, 'temp_downloaded')
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)
        dl_file = os.path.join(downloaded_data_path, fname)

        finished, i = False, 0

        while (not finished) and (i < 5):  # try max 5 times
            try:
                finished = download_era5(c, years=[sy], months=[sm], days=range(sd, d+1),
                                         h_steps=h_steps, variables=variables, grb=grb,
                                         target=dl_file, dry_run=dry_run)
                break

            except:
                # delete the partly downloaded data and retry
                os.remove(dl_file)
                finished = False
                i += 1
                continue

        if grb:
            save_gribs_from_grib(dl_file, target_path, product_name='ERA5')
        else:
            save_ncs_from_nc(dl_file, target_path, product_name='ERA5')

        if not keep_original:
            shutil.rmtree(downloaded_data_path)

        curr_start = curr_end + timedelta(days=1)


def parse_args(args):
    """
    Parse command line parameters for recursive download

    Parameters
    ----------
    args : list
        Command line parameters as list of strings

    Returns
    ----------
    clparams : argparse.Namespace
        Parsed command line parameters
    """

    parser = argparse.ArgumentParser(
        description="Download ERA 5 reanalysis data images between two dates. "
                    "Before this program can be used, you have to register at the CDS "
                    "and setup your .cdsapirc file as described here: "
                    "https://cds.climate.copernicus.eu/api-how-to")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the downloaded data will be stored.')
    parser.add_argument("-s", "--start", type=mkdate, default=datetime(1979, 1, 1),
                        help=("Startdate in format YYYY-MM-DD. "
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate, default=datetime.now(),
                        help=("Enddate in format YYYY-MM-DD. "
                              "If not given then the current date is used."))
    parser.add_argument("-var", "--variables", metavar="variables", type=str, default=None,
                        nargs="+",
                        help=("Name of variables to download "
                              "(default variables:"
                              "     evaporation, potential_evaporation, soil_temperature_level_1, "
                              "     soil_temperature_level_2, soil_temperature_level_3, soil_temperature_level_4, "
                              "     soil_type, total_precipitation, volumetric_soil_water_layer_1, "
                              "     volumetric_soil_water_layer_2, volumetric_soil_water_layer_3, "
                              "     volumetric_soil_water_layer_4, large_scale_snowfall_rate_water_equivalent,"
                              "     land_sea_mask) » "
                              "See the ERA5 documentation for more variable names: "
                              "     https://confluence.ecmwf.int/display/CKB/ERA5+data+documentation"))
    parser.add_argument("-keep", "--keep_original", type=str2bool, default='False',
                        help=("Keep the originally, temporally downloaded file as it is instread of deleting it afterwards"))
    parser.add_argument("-grb", "--as_grib", type=str2bool, default='False',
                        help=("Download data in grib format, instead of the default netcdf format"))
    parser.add_argument("--h_steps", type=int, default=None, nargs='+',
                        help=("Manually change the temporal resolution of downloaded images, must be full hours. "
                              "By default 6H images (starting at 0:00 UTC, i.e. 0 6 12 18) will be downloaded"))

    args = parser.parse_args(args)

    print("Downloading ERA5 {} data from {} to {} into folder {}"
          .format('grib' if args.as_grib is True else 'netcdf',
                  args.start.isoformat(),
                  args.end.isoformat(),
                  args.localroot))
    return args


def main(args):
    args = parse_args(args)
    download_and_move(target_path=args.localroot,
                      startdate=args.start,
                      enddate=args.end,
                      variables=args.variables,
                      h_steps=args.h_steps,
                      grb=args.as_grib,
                      keep_original=args.keep_original)


def run():
    main(sys.argv[1:])


