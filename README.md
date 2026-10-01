# Redistricting
Builds congressional districts with approximately equal populations and minimal total district perimeter.

2020 shapefiles are [here](https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/).

2020 census population files are [here](https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/).

# Usage:

The python packages used are in `requirements.txt`.

## Download and unzip data files

Let's use Texas as an example.  Click on the shapefiles link above, navigate to <ins>48_TEXAS</ins>, and then to <ins>48</ins>, and then click on <tl_2020_48_vtd20.zip>.  This is the shapefile for Texas voting districts (VTDs).  Unzip that file, perhaps into a subdirectory called `Texas`.

If you examine the contents of that zip file, you will see seven files:
```
$ unzip -l Texas/tl_2020_48_vtd20.zip
Archive:  Texas/tl_2020_48_vtd20.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        5  12-21-2020 12:54   tl_2020_48_vtd20.cpg
  2549463  12-21-2020 12:54   tl_2020_48_vtd20.dbf
      165  12-21-2020 12:54   tl_2020_48_vtd20.prj
 72730272  12-21-2020 12:54   tl_2020_48_vtd20.shp
    26668  12-21-2020 12:55   tl_2020_48_vtd20.shp.ea.iso.xml
    37431  12-21-2020 12:55   tl_2020_48_vtd20.shp.iso.xml
    72156  12-21-2020 12:54   tl_2020_48_vtd20.shx
---------                     -------
 75416160                     7 files
```

Similarly, click on the census population file link above.  Navigate to <ins>Texas</ins>, and then click on <ins>tx2020pl.zip</ins>.  Also unzip that file, into the same directory if you like.

If you examine the contents of that zip file, you will see four files:
```
$ unzip -l Texas/tx2020.pl.zip 
Archive:  Texas/tx2020.pl.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
306404146  07-26-2021 12:00   tx000012020.pl
312450134  07-26-2021 12:00   tx000022020.pl
 40905907  07-26-2021 12:00   tx000032020.pl
362246311  07-26-2021 11:59   txgeo2020.pl
---------                     -------
1022006498                     4 files
```
The one you need is `txgeo2020.pl`.

## Make a combined VTD/Population file:

Direct the program to use the population file and the VTD shapefile.  The output will also be a shapefile, so have a `.shp` on the end:
```
$ python3 ./ReadFiles.py -s Texas/tl_2020_48_vtd20.shp -p Texas/txgeo2020.pl -o Texas/vtd_pop_2020.shp
```

The `-s` option is the VTD shapefile, the `-p` option is the population file, and the `-o` option is the output shapefile.

This program will take a lot of time, as it matches the borders of VTDs to find each one's neighboring VTDs.

## Build the districts.

Once we've created the combined VTD/population shapefile, we use that as input to the next program:
```
$ python3 ./BuildDistricts.py -s Texas/jax_2020.shp -n 38 -t 0.10
```

The `-s` option points to the shapefile made by the `ReadFiles.py` program, `-n` is the number of districts (38 Congressional districts in Texas), and the `-t` option is the tolerance for the population differences between the districts, (max-min)/mean.

# TODO
1. Allow user input for State and download files.
2. Improve protrusion detection.
