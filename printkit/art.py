"""Procedural art: SDF modelling, weathering and canonical meshes. Pure functions, no file I/O.

Shapes are manifold3d.Manifold. Units mm. Measured on a 60×70×65 mm box: level_set at
0.5 mm gives ~579k triangles in ~10 s; simplify(SIMPLIFY_TOL) brings that to ~17k.
"""

import math

import manifold3d as m3
import numpy as np
import trimesh

MESH_EDGE, SIMPLIFY_TOL = 0.5, 0.05
EROSION_EDGE, MASK_RAMP, BED_CLEAR = 0.8, 1.5, 1.0
NORMAL_SMOOTHING = 12
# (wavelength mm, weight): smooth enough that simplify(SIMPLIFY_TOL) keeps parts under ~50k triangles.
OCTAVES = ((22.0, 0.45), (9.0, 0.3), (4.0, 0.25))


# ---------------------------------------------------------------- SDF primitives
# Signed distances, negative inside. `p` is an (x, y, z) tuple.


def length(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def ellipsoid(p, c, r):
    """Approximate distance to an ellipsoid with centre `c` and radii `r`."""
    x, y, z = (p[0] - c[0]) / r[0], (p[1] - c[1]) / r[1], (p[2] - c[2]) / r[2]
    k0 = length(x, y, z)
    k1 = length(x / r[0], y / r[1], z / r[2])
    return k0 * (k0 - 1) / k1 if k1 > 1e-9 else -min(r)


def capsule(p, a, b, r):
    pa = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
    ba = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    t = max(
        0.0,
        min(
            1.0,
            (pa[0] * ba[0] + pa[1] * ba[1] + pa[2] * ba[2])
            / (ba[0] ** 2 + ba[1] ** 2 + ba[2] ** 2),
        ),
    )
    return length(pa[0] - ba[0] * t, pa[1] - ba[1] * t, pa[2] - ba[2] * t) - r


def round_box(q, half, r):
    """Box with half-extents `half` and edge radius `r`; `q` is already in the box frame."""
    dx, dy, dz = (abs(q[i]) - half[i] + r for i in range(3))
    outside = length(max(dx, 0.0), max(dy, 0.0), max(dz, 0.0))
    return outside + min(max(dx, dy, dz), 0.0) - r


def triangle_2d(x, y, a, b, c):
    """Exact distance to a 2D triangle (Inigo Quilez)."""

    def sub(u, v):
        return u[0] - v[0], u[1] - v[1]

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1]

    p = (x, y)
    e0, e1, e2 = sub(b, a), sub(c, b), sub(a, c)
    v0, v1, v2 = sub(p, a), sub(p, b), sub(p, c)

    def edge(v, e):
        t = max(0.0, min(1.0, dot(v, e) / dot(e, e)))
        return v[0] - e[0] * t, v[1] - e[1] * t

    pq0, pq1, pq2 = edge(v0, e0), edge(v1, e1), edge(v2, e2)
    s = 1.0 if e0[0] * e2[1] - e0[1] * e2[0] > 0 else -1.0
    d0 = (dot(pq0, pq0), s * (v0[0] * e0[1] - v0[1] * e0[0]))
    d1 = (dot(pq1, pq1), s * (v1[0] * e1[1] - v1[1] * e1[0]))
    d2 = (dot(pq2, pq2), s * (v2[0] * e2[1] - v2[1] * e2[0]))
    dist, sign = min(d0[0], d1[0], d2[0]), min(d0[1], d1[1], d2[1])
    return -math.sqrt(dist) * (1.0 if sign > 0 else -1.0)


def smin(a, b, k):
    """Smooth union of two distances; `k` is the blend width in mm."""
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def smax(a, b, k):
    """Smooth intersection; smax(d, -cut, k) carves `cut` out of `d` with a fillet."""
    return -smin(-a, -b, k)


def level_set(distance, bounds, edge=MESH_EDGE):
    """Mesh the region where `distance(p) < 0` inside bounds (x0, y0, z0, x1, y1, z1).

    manifold3d keeps the side where its function is positive, so the distance is negated here.
    `distance` runs once per grid point in Python; cost grows with (size / edge)³.
    """
    shape = m3.Manifold.level_set(
        lambda x, y, z: -distance((x, y, z)), list(bounds), edge
    )
    if shape.status() != m3.Error.NoError:
        raise ValueError(f"level_set failed: {shape.status()}")
    return shape


# ---------------------------------------------------------------- weathering


def _lattice(seed):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(256)
    return (
        np.concatenate([perm, perm]),
        rng.random(256),
        rng.random((len(OCTAVES), 3)) * 256,
    )


def _value_noise(p, perm, values):
    cell = np.floor(p).astype(np.int64)
    f = p - cell
    u = f * f * f * (f * (f * 6 - 15) + 10)
    i, j, k = (cell[:, n] & 255 for n in range(3))
    total = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = values[perm[perm[perm[i + dx] + j + dy] + k + dz]]
                wx = u[:, 0] if dx else 1 - u[:, 0]
                wy = u[:, 1] if dy else 1 - u[:, 1]
                wz = u[:, 2] if dz else 1 - u[:, 2]
                total += h * wx * wy * wz
    return total


def weathering(points, seed):
    """Seeded fBm over an (N, 3) array, in [0, 1]; 0 = untouched, 1 = deepest pit."""
    perm, values, offsets = _lattice(seed)
    total = sum(
        weight * _value_noise(points / wavelength + offset, perm, values)
        for (wavelength, weight), offset in zip(OCTAVES, offsets)
    )
    total /= sum(weight for _, weight in OCTAVES)
    t = np.clip((total - 0.3) / 0.45, 0, 1)
    return t * t * (3 - 2 * t)


def mask_weight(points, mask):
    """1 = free to erode, 0 = protected: within BED_CLEAR of z = 0, or inside a mask box ((lo), (hi))."""
    weight = np.clip((points[:, 2] - BED_CLEAR) / MASK_RAMP, 0, 1)
    for lo, hi in mask:
        outside = np.maximum(
            np.maximum(np.asarray(lo) - points, points - np.asarray(hi)), 0
        )
        weight *= np.clip(np.linalg.norm(outside, axis=1) / MASK_RAMP, 0, 1)
    return weight


def _face_normals(verts, tris):
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    return np.cross(b - a, c - a)


def _alignment(verts, moved, tris):
    """Cosine between each triangle's normal before and after displacement."""
    before, after = _face_normals(verts, tris), _face_normals(moved, tris)
    return np.einsum("ij,ij->i", before, after) / (
        np.linalg.norm(before, axis=1) * np.linalg.norm(after, axis=1)
    )


def _vertex_normals(verts, tris):
    """Angle-weighted vertex normals, then smoothed over neighbouring vertices.

    Raw normals jump across sharp edges and fold thin triangles when displaced. Smoothing turns
    the jump into a gradual field. Weights are 1 / edge length², so vertices a sliver apart end
    up with the same normal instead of normals one graph hop apart.
    """
    face = _face_normals(verts, tris)
    face /= np.linalg.norm(face, axis=1, keepdims=True)
    normals = np.zeros_like(verts)
    for corner in range(3):
        a = verts[tris[:, corner]]
        b = verts[tris[:, (corner + 1) % 3]]
        c = verts[tris[:, (corner + 2) % 3]]
        e1, e2 = b - a, c - a
        cos = np.einsum("ij,ij->i", e1, e2) / (
            np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1)
        )
        angle = np.arccos(np.clip(cos, -1, 1))
        for axis in range(3):
            normals[:, axis] += np.bincount(
                tris[:, corner], face[:, axis] * angle, len(verts)
            )
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    src = np.concatenate(
        [tris[:, 0], tris[:, 1], tris[:, 2], tris[:, 1], tris[:, 2], tris[:, 0]]
    )
    dst = np.concatenate(
        [tris[:, 1], tris[:, 2], tris[:, 0], tris[:, 0], tris[:, 1], tris[:, 2]]
    )
    weight = 1 / (np.linalg.norm(verts[src] - verts[dst], axis=1) ** 2 + 1e-4)
    total = np.bincount(dst, weight, len(verts)) + 1 / EROSION_EDGE**2
    for _ in range(NORMAL_SMOOTHING):
        summed = normals / EROSION_EDGE**2
        for axis in range(3):
            summed[:, axis] += np.bincount(dst, normals[src, axis] * weight, len(verts))
        normals = summed / total[:, None]
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    return normals


def _unfold(verts, moved, tris, limit=0.5, rounds=200):
    """Translate each still-folded triangle rigidly: average its vertices' pushes.

    A rigid translation cannot flip a triangle, and an average of inward pushes stays inward.
    """
    for _ in range(rounds):
        folded = np.flatnonzero(_alignment(verts, moved, tris) < limit)
        if not len(folded):
            return moved
        push = moved - verts
        corners = tris[folded].ravel()
        mean = np.repeat(push[tris[folded]].mean(axis=1), 3, axis=0)
        count = np.bincount(corners, minlength=len(verts))
        touched = count > 0
        for axis in range(3):
            push[touched, axis] = (
                np.bincount(corners, mean[:, axis], len(verts))[touched]
                / count[touched]
            )
        moved = verts + push
    raise ValueError("erosion still folds triangles after relaxation")


def erode(shape, seed, amplitude, mask=()):
    """Weather `shape`: push vertices inward only, by at most `amplitude` mm (≤ 1).

    Zero displacement within BED_CLEAR of z = 0 and inside `mask` boxes, so designed clearances
    and functional faces stay valid. Run it before cutting exact functional geometry.
    """
    if not 0 < amplitude <= 1.0:
        raise ValueError(f"erosion amplitude {amplitude} mm must be in (0, 1]")
    mesh = shape.refine_to_length(EROSION_EDGE).to_mesh()
    verts = np.asarray(mesh.vert_properties[:, :3], dtype=np.float64)
    tris = np.asarray(mesh.tri_verts, dtype=np.int64)
    depth = amplitude * mask_weight(verts, mask) * weathering(verts, seed)
    moved = _unfold(verts, verts - _vertex_normals(verts, tris) * depth[:, None], tris)
    return manifold(moved, tris)


# ---------------------------------------------------------------- canonical meshes


def manifold(verts, tris):
    shape = m3.Manifold(
        m3.Mesh(
            vert_properties=np.array(verts, dtype=np.float32, order="C"),
            tri_verts=np.array(tris, dtype=np.uint32, order="C"),
        )
    )
    if shape.status() != m3.Error.NoError:
        raise ValueError(f"mesh is not a manifold: {shape.status()}")
    return shape


def _sorted_vertices(verts, tris):
    order = np.lexsort(verts.T[::-1])
    rank = np.empty_like(order)
    rank[order] = np.arange(len(order))
    return verts[order], rank[tris]


def _sorted_triangles(tris):
    start = np.argmin(tris, axis=1)[:, None]  # rotate, keeping the winding
    tris = np.take_along_axis(tris, (np.arange(3) + start) % 3, axis=1)
    return tris[np.lexsort(tris.T[::-1])]


def to_manifold(shape, tolerance=0.02, angular=0.1):
    """Tessellate a CadQuery shape into a Manifold with a canonical vertex and face order.

    OCC may mesh in parallel, so the same solid can come out with faces in a different order
    between runs; sorting keeps downstream booleans and STLs reproducible.
    """
    verts, tris = shape.val().tessellate(tolerance, angular)
    mesh = trimesh.Trimesh(
        np.array([v.toTuple() for v in verts]), np.array(tris), process=True
    )
    if not (mesh.is_watertight and mesh.volume > 0):
        raise ValueError("CadQuery shape does not tessellate to a closed solid")
    verts, tris = _sorted_vertices(
        np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces)
    )
    return manifold(verts, _sorted_triangles(tris))


def box(lo, hi):
    """Axis-aligned box Manifold from its low and high corners."""
    return m3.Manifold.cube(tuple(h - l for l, h in zip(lo, hi))).translate(tuple(lo))


def canonical_mesh(shape):
    """Vertices in coordinate order; every planar region retriangulated from its boundary.

    manifold3d's parallel booleans can triangulate a planar face with many holes differently
    from run to run: same vertices, same surface, different bytes. Rebuilding planar regions in
    a fixed order makes the output depend on the geometry only. Returns float64 vertices,
    triangles, and the number of regions left as they were because their boundary pinches at a
    vertex. Vertices used only inside a rebuilt region stay in the array, unreferenced.
    """
    mesh = shape.to_mesh()
    verts, tris = _sorted_vertices(
        np.asarray(mesh.vert_properties[:, :3], dtype=np.float64),
        np.asarray(mesh.tri_verts, dtype=np.int64),
    )
    a, b, c = (verts[tris[:, i]] for i in range(3))
    normal = np.cross(b - a, c - a)
    with np.errstate(invalid="ignore"):  # zero-area triangles get NaN normals and stay as they are
        normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    offset = np.einsum("ij,ij->i", normal, a)
    edges = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    owner = np.tile(np.arange(len(tris)), 3)
    keys = edges[:, 0] * len(verts) + edges[:, 1]
    by_key = np.argsort(keys)
    twin = by_key[np.searchsorted(keys[by_key], edges[:, 1] * len(verts) + edges[:, 0])]
    other = owner[twin]
    flat = (np.einsum("ij,ij->i", normal[owner], normal[other]) > 1 - 1e-9) & (
        np.abs(offset[owner] - offset[other]) < 1e-5
    )
    labels = trimesh.graph.connected_component_labels(
        np.column_stack([owner[flat], other[flat]]), node_count=len(tris)
    )
    keep, rebuilt, pinched = np.ones(len(tris), dtype=bool), [], 0
    for label in np.flatnonzero(np.bincount(labels) > 1):
        boundary = edges[(labels[owner] == label) & (labels[other] != label)]
        if len(np.unique(boundary[:, 0])) != len(boundary):
            pinched += 1
            continue
        step = dict(zip(boundary[:, 0].tolist(), boundary[:, 1].tolist()))
        loops = []
        while step:
            loop = [min(step)]
            while step[loop[-1]] != loop[0]:
                loop.append(step.pop(loop[-1]))
            step.pop(loop[-1])
            loops.append(np.array(loop))
        n = normal[labels == label][0]
        u = np.cross(n, (1.0, 0, 0) if abs(n[0]) < 0.9 else (0, 1.0, 0))
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        local = m3.triangulate(
            [np.column_stack([verts[loop] @ u, verts[loop] @ v]) for loop in loops]
        )
        rebuilt.append(np.concatenate(loops)[np.asarray(local)])
        keep[labels == label] = False
    return verts, _sorted_triangles(np.vstack([tris[keep], *rebuilt])), pinched
