""" Module to generate individual FRB files """

from pkg_resources import resource_filename

import numpy as np
from astropy import units

from frb import frb


def frb_121102():
    """
    FRB 121102
        All of the data currently comes from Tendulkar et al. 2017
    """
    frb121102 = frb.FRB('FRB121102', 'J053158.7+330852.5',
                        558.1*units.pc/units.cm**3,
                        z_frb=0.19273)
    # NE2001
    frb121102.set_DMISM()
    # Error ellipse
    frb121102.set_ee(0.1, 0.1, 0., 95.)
    # References
    frb121102.refs = ['Tendulkar2017']
    # Write
    frb121102.write_to_json()
    # Test
    frb121102.from_json('FRB121102.json')


def frb_180924():
    """
    FRB 180924
        All of the data currently comes from Bannister et al. 2019
    """
    frb180924 = frb.FRB('FRB180924', 'J214425.26-405400.1',
                        361.4*units.pc / units.cm**3,
                        z_frb=0.3212)
    # Error in DM (Bannister 2019)
    frb180924.DM_err = 0.06 * units.pc / units.cm**3

    # NE2001
    frb180924.set_DMISM()

    # Bannister 2019
    frb180924.fluence = 16 * units.Jy * units.ms
    frb180924.fluence_err = 1 * units.Jy * units.ms
    frb180924.RM = 14 * units.rad / units.m**2
    frb180924.RM_err = 1 * units.rad / units.m**2
    frb180924.lpol = 80.  # %
    frb180924.lpol_err = 10.
    # Error ellipse
    frb180924.set_ee(a=100./1e3, b=100./1e3, theta=0., cl=68.)

    # References
    frb180924.refs = ['Bannister2019']

    # Write
    path = resource_filename('frb', 'data/FRBs')
    frb180924.write_to_json(path=path)

def main(inflg='all'):

    if inflg == 'all':
        flg = np.sum(np.array( [2**ii for ii in range(25)]))
    else:
        flg = int(inflg)

    # 121102
    if flg & (2**0):
        frb_121102()

    # 180924
    if flg & (2**1):
        frb_180924()



# Command line execution
if __name__ == '__main__':
    # FRB 121102
    frb_121102()



