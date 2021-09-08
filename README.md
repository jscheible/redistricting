# redistricting
Builds congressional districts with approximately equal populations and minimal total district perimeter.

2020 shapefiles are downloaded from https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/

At this time, the program is hard-coded for Virginia.

# TODO
1. Generalize for all States.  (Even States with only one congresscritter can use it for State offices.)
2. Ensure Voting Districts that are defined by MultiPolygons (WHY, people?), which we now separate, are allocated to the same district.
3. Allow user input for State and number of districts.
4. Improve protrusion detection.
