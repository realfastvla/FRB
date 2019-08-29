"""DECaLS"""

import numpy as np
from astropy import units, io, utils

from frb.surveys import dlsurvey
from frb.surveys import catalog_utils

# Dependencies
try:
    from pyvo.dal import sia
except ImportError:
    print("Warning:  You need to install pyvo to retrieve DECaL images")
    _svc = None
else:
    _DEF_ACCESS_URL = "https://datalab.noao.edu/sia/des_dr1"
    _DEF_ACCESS_URL = "https://datalab.noao.edu/sia/ls_dr7"
    _svc = sia.SIAService(_DEF_ACCESS_URL)

# Define the Photometric data model for DECaL
photom = {}
photom['DECaL'] = {}
DECaL_bands = ['g', 'r', 'z', 'W1', 'W2', 'W3', 'W4']
for band in DECaL_bands:
    photom['DECaL']['DECaL_{:s}'.format(band)] = 'mag_{:s}'.format(band.lower())
    photom['DECaL']['DECaL_{:s}_err'.format(band)] = 'snr_{:s}'.format(band.lower())
photom['DECaL']['DECaL_ID'] = 'decals_id'
photom['DECaL']['ra'] = 'ra'
photom['DECaL']['dec'] = 'dec'
photom['DECaL']['DECaL_brick'] = 'brickid'


class DECaL_Survey(dlsurvey.DL_Survey):
    """
    Class to handle queries on the DECaL survey
    
    Child of DL_Survey which uses datalab to access NOAO
    
    Args:
        coord (SkyCoord): Coordiante for surveying around
        radius (Angle): Search radius around the coordinate
        
    """

    def __init__(self, coord, radius, **kwargs):
        dlsurvey.DL_Survey.__init__(self, coord, radius, **kwargs)
        self.survey = 'DECaL'
        self.bands = ['g', 'r', 'z']
        self.svc = _svc # sia.SIAService("https://datalab.noao.edu/sia/ls_dr7")
        self.qc_profile = "default"

    def get_catalog(self, query=None, query_fields=None, print_query=False,exclude_gaia=False,**kwargs):
        """
        Grab a catalog of sources around the input coordinate to the search radius
        
        Args:
            query: SQL query
            query_fields (list, optional): Over-ride list of items to query
            exclude_gaia (bool,optional): If the field 'gaia_pointsource' is present and is 1,
                                         remove those objects from the output catalog.
            print_query (bool): Print the SQL query generated 

        Returns:
            astropy.table.Table:  Catalog of sources returned

        """
        # Query
        main_cat = super(DECaL_Survey, self).get_catalog(query_fields=query_fields, print_query=print_query,**kwargs)
        #Convert SNR to mag error values.
        snr_cols = [colname for colname in main_cat.colnames if "snr" in colname]
        for col in snr_cols:
            main_cat[col] = 2.5*np.log10(1+1/main_cat[col])
        #Remove gaia objects if necessary
        if exclude_gaia:
            self.catalog = main_cat[main_cat['gaia_pointsource']==0]
        else:
            self.catalog = main_cat
        # Clean
        main_cat = catalog_utils.clean_cat(main_cat, photom['DECaL'])
        self.validate_catalog()
        # Return
        return self.catalog

    def _parse_cat_band(self, band):
        """
        Internal method to generate the bands for grabbing
        a cutout image
        
        Args:
            band (str): Band desired 

        Returns:
            list, list, str:  Table columns, Column values, band string for cutout

        """
        if band is 'g':
            bandstr = "g DECam SDSS c0001 4720.0 1520.0"
        elif band is 'r':
            bandstr = "r DECam SDSS c0002 6415.0 1480.0"
        elif band is 'z':
            bandstr = "z DECam SDSS c0004 9260.0 1520.0"
        table_cols = ['prodtype']
        col_vals = ['image']
        return table_cols, col_vals, bandstr
    
    def _gen_cat_query(self,query_fields=None):
        """
        Generate SQL query for catalog search
        
        self.query is modified in place
        
        Args:
            query_fields (list):  Override the default list for the SQL query

        """
        if query_fields is None:
            object_id_fields = ['decals_id','brick_primary','brickid','ra','dec','gaia_pointsource']
            mag_fields = ['mag_g','mag_r','mag_z','mag_w1','mag_w2','mag_w3','mag_w4']
            snr_fields = ['snr_g','snr_r','snr_z','snr_w1','snr_w2','snr_w3','snr_w4']
            query_fields = object_id_fields+mag_fields+snr_fields
        
        database = "ls_dr7.tractor"
        self.query = dlsurvey._default_query_str(query_fields, database, self.coord, self.radius)
        
    def _select_best_img(self,imgTable, verbose=True, timeout=120):
        """
        Select the best band for a cutout
        
        Args:
            imgTable: Table of images
            verbose (bool):  Print status
            timeout (int or float):  How long to wait before timing out, in seconds

        Returns:
            HDU: header data unit for the downloaded image
            
        """
        row = imgTable[0]
        url = row['access_url'].decode()
        if verbose:
            print('downloading image...')
        
        imagedat = io.fits.open(utils.data.download_file(
            url,cache=True,show_progress=False,timeout=timeout))
        return imagedat