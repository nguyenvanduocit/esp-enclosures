"""Printability of a mesh in its print orientation. Pure functions over trimesh meshes."""
import math

import numpy as np
import trimesh

from printkit.pose import euler_xyz_matrix

BED_MM = 0.01
FLAT = 0.999
ORIENTATIONS = ((0, 0, 0), (180, 0, 0), (90, 0, 0), (-90, 0, 0), (0, 90, 0), (0, -90, 0))


def _above_bed(mesh):
    return mesh.triangles_center[:, 2] > BED_MM


def overhang_area(mesh, angle=45.0):
    """Area of faces steeper than `angle` from vertical that the bed does not hold up."""
    mask = (mesh.face_normals[:, 2] < -math.cos(math.radians(angle))) & _above_bed(mesh)
    return float(mesh.area_faces[mask].sum())


def contact_area(mesh):
    mask = (mesh.face_normals[:, 2] < -FLAT) & ~_above_bed(mesh)
    return float(mesh.area_faces[mask].sum())


def bridges(mesh):
    """Connected horizontal downward regions above the bed, with their XY extent."""
    faces = np.flatnonzero((mesh.face_normals[:, 2] < -FLAT) & _above_bed(mesh))
    if not len(faces):
        return []
    edges = mesh.face_adjacency[np.isin(mesh.face_adjacency, faces).all(axis=1)]
    regions = []
    for group in trimesh.graph.connected_components(edges, nodes=faces):
        points = mesh.triangles[group].reshape(-1, 3)
        size = sorted(round(float(value), 3) for value in np.ptp(points[:, :2], axis=0))
        regions.append({'z': round(float(points[:, 2].mean()), 3), 'size_mm': size,
                        'area_mm2': round(float(mesh.area_faces[group].sum()), 2)})
    return sorted(regions, key=lambda region: (region['z'], region['area_mm2']))


def oriented(mesh, rotation):
    turned = mesh.copy()
    transform = np.eye(4)
    transform[:3, :3] = euler_xyz_matrix(rotation)
    turned.apply_transform(transform)
    turned.apply_translation([0, 0, -turned.bounds[0][2]])
    return turned


def rank_orientations(mesh, angle=45.0):
    """Six axis-aligned orientations: least overhang, then most bed contact, then lowest."""
    rows = []
    for rotation in ORIENTATIONS:
        turned = oriented(mesh, rotation)
        rows.append({'rotation': list(rotation), 'overhang_mm2': round(overhang_area(turned, angle), 1),
                     'contact_mm2': round(contact_area(turned), 1), 'height_mm': round(float(turned.extents[2]), 3)})
    # Whole mm² so tessellation noise does not reorder equivalent orientations; sort is stable.
    return sorted(rows, key=lambda row: (round(row['overhang_mm2']), -round(row['contact_mm2']), row['height_mm']))


def assess(mesh, angle=45.0):
    ranking = rank_orientations(mesh, angle)
    report = {'overhang_mm2': round(overhang_area(mesh, angle), 1), 'bridges': bridges(mesh),
              'orientations': ranking}
    if ranking[0]['rotation'] != [0, 0, 0]:
        best = ranking[0]
        report['warning'] = (f"rotating by {best['rotation']} leaves {best['overhang_mm2']} mm² overhang "
                             f"instead of {report['overhang_mm2']} mm²")
    return report
