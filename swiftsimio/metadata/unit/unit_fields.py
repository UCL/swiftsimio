"""
Contains the information for the units that determine the
particle fields. This must be provided, if not swiftsimio
will crash (as it should, you can't just be going around
having quantities without units...)

Unfortunately there must be a generator function used here
because we don't know the units ahead of time.
"""

from unyt import g, cm, s, statA, K


def generate_units(m, l, t, I, T):
    """
    Generates the unit dictionaries with the:

    mass, length, time, current, and temperature

    units respectively.
    """

    shared = {"coordinates": l, "masses": m, "particle_ids": None, "velocities": l / t}

    baryon = {
        "element_abundance": None,
        "maximal_temperature": T,
        "maximal_temperature_scale_factor": None,
        "iron_mass_frac_from_sn1a": None,
        "metal_mass_frac_from_agb": None,
        "metal_mass_frac_from_snii": None,
        "metal_mass_frac_from_sn1a": None,
        "metallicity": None,
        "smoothed_element_abundance": None,
        "smoothed_iron_mass_frac_from_sn1a": None,
        "smoothed_metallicity": None,
        "total_mass_from_agb": m,
        "total_mass_from_snii": m,
    }

    gas = {
        "density": m / (l ** 3),
        "entropy": m * l ** 2 / (t ** 2 * T),
        "internal_energy": m * l ** 2 / (t ** 2),
        "smoothing_length": l,
        "pressure": m / (l * t ** 2),
        "diffusion": None,
        "SFR": m / t,
        "temperature": T,
        "viscosity": None,
        "specific_sfr": 1 / t,
        **shared,
        **baryon,
    }

    dark_matter = {**shared}

    stars = {**shared, **baryon}

    black_holes = {**shared}

    return {
        "gas": gas,
        "dark_matter": dark_matter,
        "stars": stars,
        "black_holes": black_holes,
    }