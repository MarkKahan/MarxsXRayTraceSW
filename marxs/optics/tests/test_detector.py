import numpy as np
from astropy.table import Table

from ..detector import FlatDetector, CircularDetector
from ...tests import closeornan
from ...math.pluecker import h2e

def test_pixelnumbers():
    pos = np.array([[0, 0., -0.25, 1.],
                    [0., 9.9, 1., 1.],
                    [0., 10.1, 1., 1.]])
    dir = np.ones((3,4), dtype=float)
    dir[:, 3] = 0.
    photons = Table({'pos': pos, 'dir': dir,
                     'energy': [1,2., 3.], 'polarization': [1.,2, 3.], 'probability': [1., 1., 1.]})
    det = FlatDetector(zoom=[1., 10., 5.], pixsize=0.5)
    assert det.npix == [40, 20]
    assert det.centerpix == [19.5, 9.5]
    photons = det.process_photons(photons)
    assert closeornan(photons['det_x'], np.array([0, 9.9, np.nan]))
    assert closeornan(photons['det_y'], np.array([-0.25, 1., np.nan]))
    assert closeornan(photons['detpix_x'], np.array([19.5, 39.3, np.nan]))
    assert closeornan(photons['detpix_y'], np.array([9, 11.5, np.nan]))

    # Regression test: This was rounded down to [39, 39] at some point.
    det = FlatDetector(pixsize=0.05)
    assert det.npix == [40, 40]


def test_nonintegerwarning(recwarn):
    det = FlatDetector(zoom=np.array([1.,2.,3.]), pixsize=0.3)
    w = recwarn.pop()
    assert 'is not an integer multiple' in str(w.message)

def test_intersect_tube_miss():
    '''Rays passing at larger radius or through the center miss the tube.'''
    circ = CircularDetector()
    # Passing at larger radius
    intersect, interpos, inter_local = circ.intersect(np.array([[1., 0., .1, 0],
                                                                [-1., -1., 0., 0.]]),
                                                         np.array([[0, -1.1, 0., 1.],
                                                                   [2., 0., 0., 1.]]))
    assert np.all(intersect == False)
    assert np.all(np.isnan(interpos))
    assert np.all(np.isnan(inter_local))

    # Through the center almost parallel to z-axis
    intersect, interpos, inter_local = circ.intersect(np.array([[0., 0.1, 1., 0]]),
                                                         np.array([[0.5, 0.5, 0., 1.]]))
    assert np.all(intersect == False)
    assert np.all(np.isnan(interpos))
    assert np.all(np.isnan(inter_local))

    # Repeat with a tube that's moved to make sure we did not mess up local and
    # global coordinates in the implementation
    circ = CircularDetector(position=[0.8, 0.8, 1.2])
    intersect, interpos, inter_local = circ.intersect(np.array([[1., 0., .0, 0],
                                                                [1., 0., 0., 0.]]),
                                                         np.array([[0., 0., 0., 1.],
                                                                   [0., -0.3, 1., 1.]]))
    assert np.all(intersect == False)
    assert np.all(np.isnan(interpos))
    assert np.all(np.isnan(inter_local))

def test_intersect_tube_2points():
    dir = np.array([[-.1, 0., 0., 0], [-0.5, 0, 0., 0.], [-1., 0., 0., 0.]])
    pos = np.array([[50., 0., 0., 1.], [10., .5, 0., 1.], [2, 0, .3, 1.]])

    circ = CircularDetector(phi_offset=-np.pi)
    intersect, interpos, inter_local = circ.intersect(dir, pos)
    assert np.all(intersect == True)
    assert np.allclose(h2e(interpos), np.array([[-1., 0., 0.],
                                                [-np.sqrt(0.75), 0.5, 0.],
                                                [-1, 0., .3]]))
    assert np.allclose(inter_local, np.array([[0., -np.arcsin(0.5), 0.],
                                              [0., 0., 0.3]]).T)
    # now hit the outside. Looks very similar, if we remove the phi_offset, too.
    circ = CircularDetector(inside=False)
    intersect, interpos, inter_local = circ.intersect(dir, pos)
    assert np.all(intersect == True)
    assert np.allclose(h2e(interpos), np.array([[1., 0., 0.],
                                                [np.sqrt(0.75), 0.5, 0.],
                                                [1, 0., .3]]))
    assert np.allclose(inter_local, np.array([[0., np.arcsin(0.5), 0.],
                                              [0., 0., 0.3]]).T)

    # Repeat with a tube that's moved and zoomed to make sure we did not mess up local and
    # global coordinates in the implementation
    circ = CircularDetector(position=[0.8, 0.8, 1.2], zoom=[1, 1, 2])
    intersect, interpos, inter_local = circ.intersect(np.array([[1., 0., .0, 0],
                                                                [1., 0., 0., 0.]]),
                                                         np.array([[0., 0., 0., 1.],
                                                                   [0., 0., 1., 1.]]))
    assert np.all(intersect == True)
    assert np.allclose(h2e(interpos), np.array([[1.4, 0., 0.],
                                                [1.4, 0., 1.]]))
