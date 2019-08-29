""" Module for generating a finder chart """
import os
import numpy as np

from IPython import embed

from matplotlib import pyplot as plt

from astropy import units
from astropy.visualization.wcsaxes import SphericalCircle
from astropy.stats import sigma_clipped_stats
from astropy.visualization import LogStretch, mpl_normalize as mplnorm
from astropy.nddata import Cutout2D

from linetools import utils as ltu

from frb.figures import utils


def generate(image, wcs, title, log_stretch=False,
             cutout=None,
             primary_coord=None, secondary_coord=None,
             third_coord=None,
             vmnx=None, outfile=None):
    """
    Basic method to generate a Finder chart figure

    Args:
        image (np.ndarray):
          Image for the finder
        wcs (astropy.coordinates.wcs):
          WCS solution
        title (str):
          TItle; typically the name of the primry source
        log_stretch (bool, optional):
            Use a log stretch for the image display
        cutout (tuple, optional):
            SkyCoord (center coordinate) and Quantity (image angular size)
            for a cutout from the input image.
        primary_coord (astropy.coordinates.SkyCoord, optional):
          If provided, place a mark in red at this coordinate
        secondary_coord (astropy.coordinates.SkyCoord, optional):
          If provided, place a mark in cyan at this coordinate
          Assume it is an offset star (i.e. calculate offsets)
        third_coord (astropy.coordinates.SkyCoord, optional):
          If provided, place a mark in yellow at this coordinate
        vmnx (tuple, optional):
          Used for scaling the image.  Otherwise, the image
          is analyzed for these values.
        outfile (str, optional):
          Filename for the figure.  File type will be according
          to the extension

    Returns:
        matplotlib.pyplot.figure, matplotlib.pyplot.Axis

    """

    utils.set_mplrc()

    plt.clf()
    fig = plt.figure(dpi=600)
    fig.set_size_inches(7.5,10.5)

    # Cutout?
    if cutout is not None:
        cutout_img = Cutout2D(image, cutout[0], cutout[1], wcs=wcs)
        # Overwrite
        wcs = cutout_img.wcs
        image = cutout_img.data

    # Axis
    ax = fig.add_axes([0.10, 0.20, 0.80, 0.5], projection=wcs)

    # Show
    if log_stretch:
        norm = mplnorm.ImageNormalize(stretch=LogStretch())
    else:
        norm = None
    cimg = ax.imshow(image, cmap='Greys', norm=norm)

    # Flip so RA increases to the left
    ax.invert_xaxis()


    # N/E
    overlay = ax.get_coords_overlay('icrs')

    overlay['ra'].set_ticks(color='white')
    overlay['dec'].set_ticks(color='white')

    overlay['ra'].set_axislabel('Right Ascension')
    overlay['dec'].set_axislabel('Declination')

    overlay.grid(color='green', linestyle='solid', alpha=0.5)

    # Contrast
    if vmnx is None:
        mean, median, stddev = sigma_clipped_stats(image)  # Also set clipping level and number of iterations here if necessary
        #
        vmnx = (median-stddev, median + 2*stddev)  # sky level - 1 sigma and +2 sigma above sky level
        print("Using vmnx = {} based on the image stats".format(vmnx))
    cimg.set_clim(vmnx[0], vmnx[1])

    # Add Primary
    if primary_coord is not None:
        c = SphericalCircle((primary_coord.ra, primary_coord.dec),
                        2*units.arcsec, transform=ax.get_transform('icrs'),
                        edgecolor='red', facecolor='none')
        ax.add_patch(c)
        # Text
        jname = ltu.name_from_coord(primary_coord)
        ax.text(0.5,1.34, jname, fontsize=28,
             horizontalalignment='center',transform=ax.transAxes)

    # Secondary
    if secondary_coord is not None:
        c_S1 = SphericalCircle((secondary_coord.ra, secondary_coord.dec),
                           2*units.arcsec, transform=ax.get_transform('icrs'),
                           edgecolor='cyan', facecolor='none')
        ax.add_patch(c_S1)
        # Text
        jname = ltu.name_from_coord(secondary_coord)
        ax.text(0.5,1.24, jname, fontsize=22, color='blue',
                horizontalalignment='center',transform=ax.transAxes)
        # Print offsets
        if primary_coord is not None:
            sep = primary_coord.separation(secondary_coord).to('arcsec')
            PA = primary_coord.position_angle(secondary_coord)
            # RA/DEC
            dec_off = np.cos(PA) * sep # arcsec
            ra_off = np.sin(PA) * sep # arcsec (East is *higher* RA)
            ax.text(0.5, 1.14, 'RA(to targ) = {:.2f}  DEC(to targ) = {:.2f}'.format(
                -1*ra_off.to('arcsec'), -1*dec_off.to('arcsec')),
                     fontsize=18, horizontalalignment='center',transform=ax.transAxes)
    # Add tertiary
    if third_coord is not None:
        c = SphericalCircle((third_coord.ra, third_coord.dec),
                            2*units.arcsec, transform=ax.get_transform('icrs'),
                            edgecolor='yellow', facecolor='none')
        ax.add_patch(c)
    # Slit?
    '''
    if slit is not None:
        r = Rectangle((primary_coord.ra.value, primary_coord.dec.value),
                      slit[0]/3600., slit[1]/3600., angle=360-slit[2],
                      transform=ax.get_transform('icrs'),
                      facecolor='none', edgecolor='red')
        ax.add_patch(r)
    '''
    # Title
    ax.text(0.5, 1.44, title, fontsize=32, horizontalalignment='center', transform=ax.transAxes)

    # Sources
    # Labels
    #ax.set_xlabel(r'\textbf{DEC (EAST direction)}')
    #ax.set_ylabel(r'\textbf{RA (SOUTH direction)}')

    if outfile is not None:
        plt.savefig(outfile)
        plt.close()
    else:
        plt.show()

    # Return
    return fig, ax