# Module to run tests on surveys
#  Most of these are *not* done with Travis yet
from __future__ import print_function, absolute_import, division, unicode_literals

# TEST_UNICODE_LITERALS

import pytest
import os
import numpy as np

from astropy.coordinates import SkyCoord
from astropy import units
from astropy.table import Table

from linetools.spectra import xspectrum1d

from frb.galaxies import frbgalaxy, defs, utils

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'files')
    return os.path.join(data_dir, filename)


def test_frbhost():
    repeater_coord = SkyCoord('05h31m58.698s +33d8m52.59s', frame='icrs')  # Use as host here
    # Instantiate
    host121102 = frbgalaxy.FRBHost(repeater_coord.ra.value, repeater_coord.dec.value, '121102')
    # Add a few nebular lines  (Tendulkar+17)
    neb_lines = {}
    neb_lines['Halpha'] = 0.652e-16
    neb_lines['Halpha_err'] = 0.009e-16
    neb_lines['Halpha_Al'] = 0.622
    #
    neb_lines['Hbeta'] = 0.118e-16
    neb_lines['Hbeta_err'] = 0.011e-16
    neb_lines['Hbeta_Al'] = 0.941
    AV = 2.42
    # Deal with Galactic extinction
    for key in neb_lines.keys():
        if '_err' in key:
            continue
        if 'Al' in key:
            continue
        # Ingest
        host121102.neb_lines[key] = neb_lines[key] * 10 ** (neb_lines[key + '_Al'] * AV / 2.5)
        host121102.neb_lines[key + '_err'] = neb_lines[key + '_err'] * 10 ** (neb_lines[key + '_Al'] * AV / 2.5)
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
    # Vet
    assert host121102.vet_one('morphology')
    # Vet all
    assert host121102.vet_all()
    # Write
    outfile = data_path('test_frbhost.json')
    host121102.write_to_json(outfile=outfile)


def test_read_frbhost():
    # This test will fail if the previous failed
    host121102 = frbgalaxy.FRBHost.from_json(data_path('test_frbhost.json'))
    # Test
    assert host121102.frb == '121102'
    assert np.isclose(host121102.morphology['b/a'], 0.25)
    assert host121102.vet_all()

def test_by_name():
    host121102 = frbgalaxy.FRBHost.by_name('121102')
    assert host121102.frb == '121102'
    assert np.isclose(host121102.morphology['b/a'], 0.25)
    # with FRB
    host121102 = frbgalaxy.FRBHost.by_name('FRB121102')

def test_luminosity():
    host121102 = frbgalaxy.FRBHost.by_name('121102')
    Lum_Ha, Lum_Ha_err = host121102.calc_nebular_lum('Halpha')
    # Test
    assert Lum_Ha.unit == units.erg/units.s
    assert np.isclose(Lum_Ha.value, 2.93961853e+40)


def test_get_spectra():
    """
    Check grabbing spectra from the specDB

    Note:  This requires that specdb be installed..
    """
    try:
        import specdb
    except ImportError:
        assert True
        return
    # Check for specDB file
    if utils.load_specdb() is None:
        assert True
        return
    # Do it!
    host180924 = frbgalaxy.FRBHost.by_name('180924')
    meta, xspec = host180924.get_metaspec()
    # Test
    assert isinstance(meta, Table)
    assert isinstance(xspec, xspectrum1d.XSpectrum1D)
    assert xspec.nspec == 1
    #
    meta, xspec = host180924.get_metaspec(instr='MUSE')
    # Test
    assert isinstance(xspec, xspectrum1d.XSpectrum1D)
    assert xspec.nspec == 1
    #
    meta, xspecs = host180924.get_metaspec(return_all=True)
    assert xspecs.nspec == 2
