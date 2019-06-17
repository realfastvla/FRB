""" Module for building specdb files related to FRB spectra
"""
from __future__ import print_function, absolute_import, division, unicode_literals

import numpy as np
import os
from IPython import embed
import h5py

import glob

from pkg_resources import resource_filename

from astropy.coordinates import SkyCoord
from astropy.coordinates import match_coordinates_sky
from astropy import units
from astropy.table import Table

from specdb import defs
from specdb.build import privatedb as pbuild
from specdb.build import utils as spbu

from frb.surveys import sdss

all_instruments = ['SDSS']
spectra_path = resource_filename('frb', '../Spectra')

def grab_files(all_files, instrument):
    # Setup
    base_files = [os.path.basename(ifile) for ifile in all_files]
    file_subset = []
    # Simple loop 
    for kk, ifile in enumerate(base_files):
        if instrument in ifile:
            file_subset.append(all_files[kk])
    # Return
    return file_subset


def sdss_redshifts():
    """
    Enter the SDSS directory and build a redshift table
    based on the spectra present

    Returns:

    """
    #
    all_folders = glob.glob(spectra_path+'/SDSS/*')
    Jnames = []
    for folder in all_folders:
        # Grab the list of spectra files
        spec_files = glob.glob(os.path.join(folder, 'J*.fits'))
        # Generate the name list
        Jnames += [os.path.basename(ifile).split('_')[0] for ifile in spec_files]
    # Coords
    coords = SkyCoord(Jnames, unit=(units.hourangle, units.deg))  # from DES
    # Setup
    done = np.zeros_like(coords.ra.value, dtype=bool)
    zs = np.zeros_like(coords.ra.value)

    # Loop me
    while np.any(~done):
        # Grab the first not done
        i0 = np.where(~done)[0][0]
        coord = coords[i0]
        # Grab the SDSS data
        sdssSurvey = sdss.SDSS_Survey(coord, 10*units.arcmin)
        #
        sub_coords = coords[~done]
        sep = coord.separation(sub_coords)
        doidx = np.where(sep < 10*units.arcmin)[0]
        dothem = coords[doidx]
        # Now match
        catalog = sdssSurvey.get_catalog()
        sdss_coords = SkyCoord(ra=catalog['ra'], dec=catalog['dec'], unit='deg')
        idx, d2d, d3d = match_coordinates_sky(dothem, sdss_coords, nthneighbor=1)
        # Fill
        zs[doidx] = catalog['z_spec'][idx]
        done[np.where(dothem)] = True

    # Write the catalog
    tbl = Table()
    tbl['ra'] = coords.ra.value
    tbl['dec'] = coords.dec.value
    tbl['z'] = zs
    tbl['z_source'] = 'SDSS'
    tbl.write('z_SDSS.ascii', overwrite=True, format='ascii.fixed_width')

    
def generate_by_refs(input_refs, outfile):
    # Not elegant but it works
    all_folders = glob.glob(spectra_path+'/*/*')
    all_refs = [os.path.basename(ifolder) for ifolder in all_folders]
    
    # Loop in input refs
    all_spec_files = []
    for ref in input_refs:
        idx = all_refs.index(ref)
        # Grab the list of spectra
        specs = glob.glob(os.path.join(all_folders[idx], '*.fits'))
        # Save
        all_spec_files += specs
    
    # Get it started
    # HDF5 file
    hdf = h5py.File(outfile, 'w')

    # Defs
    zpri = defs.z_priority()

    # Main DB Table
    id_key = 'FRB_ID'
    maindb, tkeys = spbu.start_maindb(id_key)
    gdict = {}

    # Loop on Instruments
    for instr in all_instruments:
        fits_files = grab_files(all_spec_files, instr)
        if len(fits_files) == 0:
            continue
        # Option dicts
        mwargs = {}
        mwargs['toler'] = 1.0 * u.arcsec  # Require an 
        skipz = False
        # Meta
        parse_head, mdict, fname = None, None, True
        if instr == 'SDSS':  # Spectra with Continua only
            mdict = dict(DISPERSER='BOTH', R=2000., TELESCOPE='SDSS 2.5-M', INSTR='SDSS')
            parse_head = {'DATE-OBS': 'DATE-OBS'}
            maxpix = 4000

        # Meta
        full_meta = pbuild.mk_meta(fits_files, ztbl, mdict=mdict, fname=fname,
                                   verbose=True, parse_head=parse_head, skip_badz=skipz,
                                   chkz=True, **mwargs)


        embed()

if __name__ == '__main__':

    # Test
    #generate_by_refs(['DR7'], 'tst_specdb.hdf5')
    sdss_redshifts()
