import geopandas as gpd
import geojson
import json
import numpy as np
import os
import pyproj
import shapely
import shapely.wkt

from functools import partial
from shapely.ops import transform
from shapely.geometry import shape
from osgeo import gdal, gdal_array, gdalconst

        
def get_utm_zone(latitude, longitude):
    """
    compute utm zone and weather it is in North or South given by a lat/lon coordinate

    Args
      longitude : float
      latitude : float

    Returns
      utm_zone, is_north : list (or list like)
      utm zone number and N or S string

    """

    utm_zone = int(1 + (longitude + 180.0) / 6.0)

    is_north = 0
    if (latitude < 0.0):
        is_north = "S";
    else:
        is_north = "N";

    return utm_zone, is_north

def convert_geometrywkt_to_coords(geometry_wkt):
    """
    converting field boundary geometry in well known text format into
        list of coordinates to query images especially from GIPPer. CRS is given by WGS84
    Args
      geometry_str : string

    Returns
      coords : list (or list like)
    """
    geometry = shapely.wkt.loads(geometry_wkt)
    g = geojson.Feature(geometry=geometry, properties={})
    coords = g.geometry["coordinates"]

    return coords

def convert_wkt_to_geometry(geometry_wkt):

    # Convert to a shapely.geometry.polygon.Polygon object
    geom = shapely.wkt.loads(geometry_wkt)

    return geom


def convert_wkt_to_geojson(geometry_wkt):
    
    g1 = shapely.wkt.loads(geometry_wkt)
    g2 = shapely.geometry.mapping(g1)
    geojson_str = json.dumps(g2)

    return geojson_str


def compute_centroid_from_geometry(geometry_wkt):
    """
    compute centroid of a geometry; can be polygon, point

    Args
      geometry : str
      geojson geometry string

    Returns
      y, x: latitude and longitude of centroid

    """

    geometry = shapely.wkt.loads(geometry_wkt)
    x = geometry.centroid.x
    y = geometry.centroid.y

    return y, x

def convert_geojson_to_wkt(boundary):
    """
    Returns wkt geometry from geojson 

    Parameters:
    ----------
    geojson : json
        geojson 

    Returns:
    -------
    geometry wkt : wkt 
    """    
    
    s = json.dumps(boundary)
    # convert to geojson.geometry.Polygon
    geo = geojson.loads(s)
    # Feed to shape() to convert to shapely.geometry.polygon.Polygon
    geom = shape(geo)
    # get a WKTrepresentation
    return geom.wkt
    
def get_country_state(aoi): 
    """
    Returns the reverse geocode for the input aoi. 

    Parameters:
    ----------
    aoi : shapely geometry
          polygon field geometry.

    Returns:
    -------
    rev_geocode : 
              reverse geocode for the  where the polygon geometry is from 
    """    
    
    cntr = aoi.centroid
    cntr = cntr.__geo_interface__['coordinates']
    rev_geocode = reverse_geocode_coords(cntr[::-1])
    return rev_geocode

def image_query_start_end_datetime(planting_date):
    """
    obtain time window of start and end dates in isoformat datetime string

    Args
      date_str : string
         a start date in "2018-09-10" format (%Y-%m-%d)

    Returns
      start_date, end_date : tuple
          a tuple with a 2 weeks time window for image query throught GIPPer

    """
    # define number of max day to search
    N = 14

    start_date = datetime.strptime(planting_date, "%Y-%m-%d")
    start_date_iso = datetime.strptime(planting_date, "%Y-%m-%d").isoformat()
    end_date_iso = (start_date + timedelta(days=N)).isoformat()

    return start_date_iso, end_date_iso


def convert_geom_latlon_to_utm_na(geometry, utmzone):
    """

    """
    source_crs = 'epsg:4326'
    target_crs = 'epsg:326{}'.format(utmzone)

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    utm_geom = transform(project, geometry)  # apply projection
    return utm_geom

def convert_geom_latlon_to_utm_sa(geometry, utmzone):
    """

    """
    source_crs = 'epsg:4326'
    target_crs = 'epsg:327{}'.format(utmzone)

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    utm_geom = transform(project, geometry)  # apply projection
    return utm_geom

def convert_geom_utm_to_latlog(geometry, inputcrs):

    source_crs = inputcrs
    target_crs = 'epsg:4326'

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    latlon_geom = transform(project, geometry)  # apply projection
    return latlon_geom