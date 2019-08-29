""" Top-level module to build or re-build the JSON files for
FRB host galaxies"""

from pkg_resources import resource_filename
import os
import sys

from IPython import embed

import numpy as np

from astropy.coordinates import SkyCoord
from astropy import units
from astropy.table import Table

from frb.galaxies import frbgalaxy, defs
from frb.galaxies import photom as frbphotom
from frb.surveys import des

db_path = os.getenv('FRB_GDB')
if db_path is None:
    embed(header='You need to set $FRB_GDB')


def build_host_121102(build_photom=False):
    """
    Generate the JSON file for FRB 121102

    Writes to 121102/FRB121102_host.json

    All of the data currently comes from Tendulkar et al. 2017

    Args:
        build_photom (bool, optional): Generate the photometry file in the Galaxy_DB

    """
    FRB_coord = SkyCoord('05h31m58.698s +33d8m52.59s', frame='icrs')
    # Eyeball Tendulkar+17 PA
    gal_coord = FRB_coord.directional_offset_by(-45 * units.deg, 286e-3 * units.arcsec)

    # Instantiate
    host121102 = frbgalaxy.FRBHost(gal_coord.ra.value, gal_coord.dec.value, '121102')

    # Redshift
    host121102.set_z(0.19273, 'spec', err=0.00008)

    # Photometry -- Tendulkar 2017
    photom_file = os.path.join(db_path, 'Repeater', 'Tendulkar2017', 'tendulkar2017_photom.ascii')
    if build_photom:
        photom = Table()
        #photom['Name'] = ['HG121102']  DO NOT USE str columns!
        photom['ra'] = [host121102.coord.ra.value]
        photom['dec'] = host121102.coord.dec.value
        #
        photom['GMOS_r'] = 25.1
        photom['GMOS_r_err'] = 0.1
        photom['GMOS_i'] = 23.9
        photom['GMOS_i_err'] = 0.1
        # Write
        photom = frbphotom.merge_photom_tables(photom, photom_file)
        embed(header='60')
        photom.write(photom_file, format=frbphotom.table_format, overwrite=True)
    host121102.parse_photom(Table.read(photom_file, format=frbphotom.table_format))

    # Nebular lines
    neb_lines = {}
    neb_lines['Halpha'] = 0.652e-16
    neb_lines['Halpha_err'] = 0.009e-16
    neb_lines['Halpha_Al'] = 0.622
    #
    neb_lines['Hbeta'] = 0.118e-16
    neb_lines['Hbeta_err'] = 0.011e-16
    neb_lines['Hbeta_Al'] = 0.941
    #
    neb_lines['[OIII] 5007'] = 0.575e-16
    neb_lines['[OIII] 5007_err'] = 0.011e-16
    neb_lines['[OIII] 5007_Al'] = 0.911
    #
    neb_lines['[NII] 6584'] = 0.030e-16  # * units.erg/units.cm**2/units.s      # Upper limit
    neb_lines['[NII] 6584_err'] = -999.  # * units.erg/units.cm**2/units.s      # Upper limit
    neb_lines['[NII] 6584_Al'] = 0.619

    AV = 2.42

    # Extinction correct
    for key in neb_lines.keys():
        if '_err' in key:
            continue
        if 'Al' in key:
            continue
        # Ingest
        host121102.neb_lines[key] = neb_lines[key] * 10 ** (neb_lines[key + '_Al'] * AV / 2.5)
        if neb_lines[key + '_err'] > 0:
            host121102.neb_lines[key + '_err'] = neb_lines[key + '_err'] * 10 ** (neb_lines[key + '_Al'] * AV / 2.5)
        else:
            host121102.neb_lines[key + '_err'] = neb_lines[key + '_err']

    # Vette
    for key in host121102.neb_lines.keys():
        if '_err' in key:
            continue
        assert key in defs.valid_neb_lines

    # Morphology
    host121102.morphology['reff_ang'] = 0.41
    host121102.morphology['reff_ang_err'] = 0.06
    #
    host121102.morphology['n'] = 2.2
    host121102.morphology['n_err'] = 1.5
    #
    host121102.morphology['b/a'] = 0.25
    host121102.morphology['b/a_err'] = 0.13

    # Derived quantities
    host121102.derived['M_r'] = -17.0  # AB; Tendulkar+17
    host121102.derived['M_r_err'] = 0.2  # Estimated by JXP
    host121102.derived['SFR_nebular'] = 0.23  # MSun/yr; Tendulkar+17
    host121102.derived['Mstar'] = 5.5e7  # Msun; Tendulkar+17
    host121102.derived['Mstar_err'] = 1.5e7  # Msun; Tendulkar+17
    host121102.derived['Z_spec'] = -0.16  # Tendulkar+17 on a scale with Solar O/H = 8.86
    host121102.derived['Z_spec_err'] = -999.  # Tendulkar+17

    # Vet
    assert host121102.vet_all()

    # Write
    path = resource_filename('frb', 'data/Galaxies/121102')
    host121102.write_to_json(path=path, overwrite=True)


def build_host_180924(build_photom=True):
    """
    Generate the JSON file for FRB 180924
    
    All data are from Bannister et al. 2019

    Writes to 180924/FRB180924_host.json

    Args:
        build_photom (bool, optional): Generate the photometry file in the Galaxy_DB
    """
    gal_coord = SkyCoord('J214425.25-405400.81', unit=(units.hourangle, units.deg))

    # Instantiate
    host = frbgalaxy.FRBHost(gal_coord.ra.value, gal_coord.dec.value, '180924')

    # Redshift
    host.set_z(0.3212, 'spec')

    # Morphology
    host.parse_galfit(os.path.join(db_path, 'CRAFT', 'Bannister2019',
                                   'HG180924_DES_galfit.log'), 0.263)

    # Photometry

    # DES
    # Grab the table (requires internet)
    photom_file = os.path.join(db_path, 'CRAFT', 'Bannister2019', 'bannister2019_photom.ascii')
    if build_photom:
        search_r = 2*units.arcsec
        des_srvy = des.DES_Survey(gal_coord, search_r)
        des_tbl = des_srvy.get_catalog(print_query=True)
        # Write
        des_tbl.write(photom_file, format=frbphotom.table_format)
    else:
        des_tbl = Table.read(photom_file, format=frbphotom.table_format)

    # Parse
    host.parse_photom(des_tbl)

    # PPXF
    host.parse_ppxf(os.path.join(db_path, 'CRAFT', 'Bannister2019', 'HG180924_MUSE_ppxf.ecsv'))

    # Derived quantities

    # AV
    host.calc_nebular_AV('Ha/Hb')

    # SFR
    host.calc_nebular_SFR('Ha')
    host.derived['SFR_nebular_err'] = -999.

    # CIGALE
    host.parse_cigale(os.path.join(db_path, 'CRAFT', 'Bannister2019',
                                   'HG180924_CIGALE.fits'), 0.263)

    # Vet all
    host.vet_all()

    # Write
    path = resource_filename('frb', 'data/Galaxies/180924')
    host.write_to_json(path=path)
    
    
def main(inflg='all'):

    if inflg == 'all':
        flg = np.sum(np.array( [2**ii for ii in range(25)]))
    else:
        flg = int(inflg)

    # 121102
    if flg & (2**0):
        build_host_121102(build_photom=True)

    # 180924
    if flg & (2**1):
        build_host_180924(build_photom=True)


# Command line execution
if __name__ == '__main__':
    pass

