""" utils related to SurveyCoord objects"""

from frb.surveys.sdss import SDSS_Survey
from frb.surveys.des import DES_Survey
from frb.surveys.wise import WISE_Survey
from frb.surveys.decals import DECaL_Survey
from frb.surveys.psrcat import PSRCAT_Survey
from frb.surveys import heasarc
from frb.surveys.panstarrs import Pan_STARRS_Survey

allowed_surveys = ['SDSS', 'DES', 'NVSS', 'FIRST', 'WENSS', 'DECaL', 'PSRCAT', 'WISE', 'Pan-STARRS']


def load_survey_by_name(name, coord, radius, **kwargs):
    """
    Load up a Survey class object for the named survey
    allowed_surveys = ['SDSS', 'DES', 'NVSS', 'FIRST', 'WENSS', 'DECaL', 'PSRCAT', 'WISE', 'Pan-STARRS']

    Args:
        name (str): Name of the survey 
        coord (astropy.coordiantes.SkyCoord): Coordinate to define survey around 
        radius (astropy.units.Quanity): Outer radius of the survey
        **kwargs: Passed the Survey object

    Returns:
        frb.surveys.SurveyCoord: Child of this parent given by input survey name

    """

    if name not in allowed_surveys:
        raise IOError("Not ready for input survey.\n These are allowed: {}".format(allowed_surveys))

    # Do it
    if name == 'SDSS':
        survey = SDSS_Survey(coord, radius, **kwargs)
    elif name == 'DES':
        survey = DES_Survey(coord, radius, **kwargs)
    elif name == 'NVSS':
        survey = heasarc.NVSS_Survey(coord, radius, **kwargs)
    elif name == 'WENSS':
        survey = heasarc.WENSS_Survey(coord, radius, **kwargs)
    elif name == 'FIRST':
        survey = heasarc.FIRST_Survey(coord, radius, **kwargs)
    elif name == 'DECaL':
        survey = DECaL_Survey(coord, radius, **kwargs)
    elif name == 'WISE':
        survey = WISE_Survey(coord, radius, **kwargs)
    elif name == 'PSRCAT':
        survey = PSRCAT_Survey(coord, radius, **kwargs)
    elif name == 'Pan-STARRS':
        survey = Pan_STARRS_Survey(coord,radius,**kwargs)

    # Return
    return survey


