import numpy as np 
import h5py

from pysisyphus.Geometry import Geometry
from pysisyphus.helpers_pure import eigval_to_wavenumber


def save_hessian(h5_fn, geom, cart_hessian=None, energy=None, mult=None):
    if cart_hessian is None:
        cart_hessian = geom.cart_hessian

    if energy is None:
        energy = geom.energy

    if mult is None:
        mult = geom.calculator.mult

    if len(geom.atoms) > 1:
        proj_hessian = geom.eckart_projection(geom.mass_weigh_hessian(cart_hessian))
    else:
        proj_hessian = cart_hessian
    eigvals, _ = np.linalg.eigh(proj_hessian)
    vibfreqs = eigval_to_wavenumber(eigvals)

    masses = geom.masses
    atoms = geom.atoms
    coords3d = geom.coords3d

    with h5py.File(h5_fn, "w") as handle:
        handle.create_dataset("hessian", data=cart_hessian)
        handle.create_dataset("vibfreqs", data=vibfreqs)
        handle.create_dataset("masses", data=masses)
        handle.create_dataset("coords3d", data=coords3d)

        try:
            handle.attrs["atoms"] = [atom.lower() for atom in atoms]
        except OSError:
            handle.create_dataset("atoms", data=[atom.lower() for atom in atoms])
        handle.attrs["energy"] = energy
        handle.attrs["mult"] = mult


def save_third_deriv(h5_fn, geom, third_deriv_result, H_mw, H_proj):
    with h5py.File(h5_fn, "w") as handle:
        for key, value in third_deriv_result._asdict().items():
            handle.create_dataset(key, data=value)

        handle.create_dataset("coords3d", data=geom.coords3d)
        handle.create_dataset("masses", data=geom.masses)
        handle.create_dataset("H_mw", data=H_mw)
        handle.create_dataset("H_proj", data=H_proj)
        try:
            handle.attrs["atoms"] = [atom.lower() for atom in atoms]
        except OSError:
            handle.create_dataset("atoms", data=[atom.lower() for atom in atoms])


def geom_from_hessian(h5_fn, **geom_kwargs):
    with h5py.File(h5_fn, "r") as handle:
        try:
            atoms = [atom.capitalize() for atom in handle.attrs["atoms"]]
        except (KeyError, TypeError):
            atoms = [atom.capitalize() for atom in handle["atoms"][:]]
        coords3d = handle["coords3d"][:]
        energy = handle.attrs["energy"]
        cart_hessian = handle["hessian"][:]

    geom = Geometry(atoms=atoms, coords=coords3d, **geom_kwargs)
    geom.cart_hessian = cart_hessian
    geom.energy = energy
    return geom
