import pytest
from swiftsimio import load
from swiftsimio.visualisation import scatter, slice, volume_render
from swiftsimio.visualisation.projection import (
    scatter_parallel,
    project_gas,
    project_pixel_grid,
)
from swiftsimio.visualisation.slice import slice_scatter_parallel, slice_gas
from swiftsimio.visualisation.volume_render import render_gas
from swiftsimio.visualisation.projection_backends import backends, backends_parallel
from swiftsimio.visualisation.smoothing_length_generation import (
    generate_smoothing_lengths,
)
from swiftsimio.optional_packages import CudaSupportError, CUDA_AVAILABLE
from swiftsimio.objects import cosmo_factor, a

from tests.helper import requires

import numpy as np


try:
    from matplotlib.pyplot import imsave
except:
    pass


def test_scatter(save=False):
    """
    Tests the scatter functions from all backends.
    """

    for backend in backends.keys():
        try:
            image = backends[backend](
                np.array([0.0, 1.0, 1.0, -0.000001]),
                np.array([0.0, 0.0, 1.0, 1.000001]),
                np.array([1.0, 1.0, 1.0, 1.0]),
                np.array([0.2, 0.2, 0.2, 0.000002]),
                256,
            )
        except CudaSupportError:
            if CUDA_AVAILABLE:
                raise ImportError("Optional loading of the CUDA module is broken")
            else:
                continue

    if save:
        imsave("test_image_creation.png", image)

    return


def test_scatter_mass_conservation():
    np.random.seed(971263)
    # Width of 0.8 centered on 0.5, 0.5.
    x = 0.8 * np.random.rand(100) + 0.1
    y = 0.8 * np.random.rand(100) + 0.1
    m = np.ones_like(x)
    h = 0.05 * np.ones_like(x)

    resolutions = [8, 16, 32, 64, 128, 256, 512]
    total_mass = np.sum(m)

    for resolution in resolutions:
        image = scatter(x, y, m, h, resolution)
        mass_in_image = image.sum() / (resolution ** 2)

        # Check mass conservation to 5%
        assert np.isclose(mass_in_image, total_mass, 0.05)

    return


def test_scatter_parallel(save=False):
    """
    Asserts that we create the same image with the parallel version of the code
    as with the serial version.
    """

    number_of_parts = 1000
    h_max = np.float32(0.05)
    resolution = 512

    coordinates = (
        np.random.rand(2 * number_of_parts)
        .reshape((2, number_of_parts))
        .astype(np.float64)
    )
    hsml = np.random.rand(number_of_parts).astype(np.float32) * h_max
    masses = np.ones(number_of_parts, dtype=np.float32)

    image = scatter(coordinates[0], coordinates[1], masses, hsml, resolution)
    image_par = scatter_parallel(
        coordinates[0], coordinates[1], masses, hsml, resolution
    )

    if save:
        imsave("test_image_creation.png", image)

    assert np.isclose(image, image_par).all()

    return


def test_slice(save=False):
    image = slice(
        np.array([0.0, 1.0, 1.0, -0.000001]),
        np.array([0.0, 0.0, 1.0, 1.000001]),
        np.array([0.0, 0.0, 1.0, 1.000001]),
        np.array([1.0, 1.0, 1.0, 1.0]),
        np.array([0.2, 0.2, 0.2, 0.000002]),
        0.99,
        256,
    )

    if save:
        imsave("test_image_creation.png", image)

    return


def test_slice_parallel(save=False):
    """
    Asserts that we create the same image with the parallel version of the code
    as with the serial version.
    """

    number_of_parts = 1000
    h_max = np.float32(0.05)
    z_slice = 0.5
    resolution = 256

    coordinates = (
        np.random.rand(3 * number_of_parts)
        .reshape((3, number_of_parts))
        .astype(np.float64)
    )
    hsml = np.random.rand(number_of_parts).astype(np.float32) * h_max
    masses = np.ones(number_of_parts, dtype=np.float32)

    image = slice(
        coordinates[0],
        coordinates[1],
        coordinates[2],
        masses,
        hsml,
        z_slice,
        resolution,
    )
    image_par = slice_scatter_parallel(
        coordinates[0],
        coordinates[1],
        coordinates[2],
        masses,
        hsml,
        z_slice,
        resolution,
    )

    if save:
        imsave("test_image_creation.png", image)

    assert np.isclose(image, image_par).all()

    return


def test_volume_render():
    image = volume_render.scatter(
        np.array([0.0, 1.0, 1.0, -0.000001]),
        np.array([0.0, 0.0, 1.0, 1.000001]),
        np.array([0.0, 0.0, 1.0, 1.000001]),
        np.array([1.0, 1.0, 1.0, 1.0]),
        np.array([0.2, 0.2, 0.2, 0.000002]),
        64,
    )

    return


def test_volume_parallel():
    number_of_parts = 1000
    h_max = np.float32(0.05)
    resolution = 64

    coordinates = (
        np.random.rand(3 * number_of_parts)
        .reshape((3, number_of_parts))
        .astype(np.float64)
    )
    hsml = np.random.rand(number_of_parts).astype(np.float32) * h_max
    masses = np.ones(number_of_parts, dtype=np.float32)

    image = volume_render.scatter(
        coordinates[0], coordinates[1], coordinates[2], masses, hsml, resolution
    )
    image_par = volume_render.scatter_parallel(
        coordinates[0], coordinates[1], coordinates[2], masses, hsml, resolution
    )

    assert np.isclose(image, image_par).all()

    return


@requires("cosmological_volume.hdf5")
def test_selection_render(filename):
    data = load(filename)
    bs = data.metadata.boxsize[0]

    # Projection
    render_full = project_gas(data, 256, parallel=True)
    render_partial = project_gas(
        data, 256, parallel=True, region=[0.25 * bs, 0.75 * bs] * 2
    )
    render_tiny = project_gas(data, 256, parallel=True, region=[0 * bs, 0.001 * bs] * 2)

    # Slicing
    render_full = slice_gas(data, 256, z_slice=0.5 * bs, parallel=True)
    render_partial = slice_gas(
        data, 256, z_slice=0.5 * bs, parallel=True, region=[0.25 * bs, 0.75 * bs] * 2
    )
    render_tiny = slice_gas(
        data, 256, z_slice=0.5 * bs, parallel=True, region=[0 * bs, 0.001 * bs] * 2
    )
    # Test for non-square slices
    render_nonsquare = slice_gas(
        data,
        256,
        z_slice=0.5 * bs,
        parallel=True,
        region=[0 * bs, 0.001 * bs, 0.25 * bs, 0.75 * bs],
    )

    # If they don't crash we're happy!

    return


def test_render_outside_region():
    """
    Tests what happens when you use `scatter` on a bunch of particles that live
    outside of the image.
    """

    number_of_parts = 10000
    resolution = 256

    x = np.random.rand(number_of_parts) - 0.5
    y = np.random.rand(number_of_parts) - 0.5
    z = np.random.rand(number_of_parts) - 0.5
    h = 10 ** np.random.rand(number_of_parts) - 1.0
    h[h > 0.5] = 0.05
    m = np.ones_like(h)
    backends["histogram"](x, y, m, h, resolution)

    for backend in backends_parallel.keys():
        try:
            backends[backend](x, y, m, h, resolution)
        except CudaSupportError:
            if CUDA_AVAILABLE:
                raise ImportError("Optional loading of the CUDA module is broken")
            else:
                continue

    slice_scatter_parallel(x, y, z, m, h, 0.2, resolution)

    volume_render.scatter_parallel(x, y, z, m, h, resolution)


@requires("cosmological_volume.hdf5")
def test_comoving_versus_physical(filename):
    """
    Test what happens if you try to mix up physical and comoving quantities.
    """

    for func, aexp in [(project_gas, -2.0), (slice_gas, -3.0), (render_gas, -3.0)]:
        # normal case: everything comoving
        data = load(filename)
        # we force the default (project="masses") to check the cosmo_factor
        # conversion in this case
        img = func(data, resolution=256, project=None)
        assert img.comoving
        assert img.cosmo_factor.expr == a ** aexp
        img = func(data, resolution=256, project="densities")
        assert img.comoving
        assert img.cosmo_factor.expr == a ** (aexp - 3.0)
        # try to mix comoving coordinates with a physical variable
        data.gas.densities.convert_to_physical()
        with pytest.raises(AttributeError, match="not compatible with comoving"):
            img = func(data, resolution=256, project="densities")
        # convert coordinates to physical (but not smoothing lengths)
        data.gas.coordinates.convert_to_physical()
        with pytest.raises(AttributeError, match=""):
            img = func(data, resolution=256, project="masses")
        # also convert smoothing lengths to physical
        data.gas.smoothing_lengths.convert_to_physical()
        # masses are always compatible with either
        img = func(data, resolution=256, project="masses")
        # check that we get a physical result
        assert not img.comoving
        assert img.cosmo_factor.expr == a ** aexp
        # densities are still compatible with physical
        img = func(data, resolution=256, project="densities")
        assert not img.comoving
        assert img.cosmo_factor.expr == a ** (aexp - 3.0)
        # now try again with comoving densities
        data.gas.densities.convert_to_comoving()
        with pytest.raises(AttributeError, match="not compatible with physical"):
            img = func(data, resolution=256, project="densities")


@requires("cosmological_volume.hdf5")
def test_nongas_smoothing_lengths(filename):
    """
    Test that the visualisation tools to calculate smoothing lengths give usable results.
    """

    data = load(filename)
    data.dark_matter.smoothing_length = generate_smoothing_lengths(
        data.dark_matter.coordinates, data.metadata.boxsize, kernel_gamma=1.8
    )
    project_pixel_grid(
        data.dark_matter,
        boxsize=data.metadata.boxsize,
        resolution=256,
        project="masses",
    )

    # if project_pixel_grid runs without error the smoothing lengths seem usable
    return
