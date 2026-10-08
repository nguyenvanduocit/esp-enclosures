"""Render the CAD geometry, including an illustrative board, to preview.png."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from trimesh import Trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from model import OUT, export_and_verify, installed_lid

BG = "#f4f1ea"
INK = "#20363d"
TEAL = "#367c85"
CREAM = "#e2d8bf"


def draw(ax, parts):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(*to_rgb(BG))
    for part, color, offset in parts:
        points, triangles = part.val().tessellate(0.07, 0.15)
        vertices = np.array([p.toTuple() for p in points]) + np.array(offset)
        mesh = Trimesh(vertices=vertices, faces=triangles)
        mesh.fix_normals()
        vtk_points = vtk.vtkPoints()
        vtk_points.SetData(numpy_to_vtk(mesh.vertices, deep=True))
        cells = np.column_stack((np.full(len(mesh.faces), 3), mesh.faces)).astype(np.int64).ravel()
        vtk_cells = vtk.vtkCellArray()
        vtk_cells.SetCells(len(mesh.faces), numpy_to_vtkIdTypeArray(cells, deep=True))
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        polydata.SetPolys(vtk_cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.SetFeatureAngle(35)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*to_rgb(color))
        actor.GetProperty().SetAmbient(0.30)
        actor.GetProperty().SetDiffuse(0.70)
        renderer.AddActor(actor)
    camera = renderer.GetActiveCamera()
    camera.SetPosition(75, -110, 95)
    camera.SetFocalPoint(0, 0, 16)
    camera.SetViewUp(0, 0, 1)
    camera.ParallelProjectionOn()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1000, 1050)
    window.SetMultiSamples(8)
    window.AddRenderer(renderer)
    renderer.ResetCamera()
    camera.Zoom(1.12)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.ReadFrontBufferOff()
    capture.Update()
    pixels = capture.GetOutput()
    w, h, _ = pixels.GetDimensions()
    rgb = vtk_to_numpy(pixels.GetPointData().GetScalars()).reshape(h, w, -1)
    ax.imshow(np.flipud(rgb))
    ax.set_axis_off()
    window.Finalize()


def main():
    base, lid, board = export_and_verify()
    fig = plt.figure(figsize=(15, 9.5), facecolor=BG)
    fig.text(0.055, 0.93, "ESP32-C3", fontsize=34, weight="bold", color=INK)
    fig.text(0.055, 0.884, "SUPERMINI  /  HEADER-PIN ENCLOSURE", fontsize=12, color=TEAL, weight="bold")
    fig.text(0.94, 0.937, "PROTOTYPE 01", ha="right", fontsize=11, color=INK)
    fig.text(0.94, 0.91, "26.4 × 32 × 20.2 mm", ha="right", fontsize=14, color=INK)

    assembled = fig.add_axes((0.035, 0.47, 0.44, 0.38))
    draw(assembled, [(base, TEAL, (0, 0, 0)), (installed_lid(lid), CREAM, (0, 0, 0))]
         + [(shape, color, (0, 0, 0)) for _, shape, color in board])
    fig.text(0.065, 0.45, "01  ASSEMBLED", fontsize=11, weight="bold", color=INK)
    fig.text(0.065, 0.423, "USB-C opening · removable vented lid", fontsize=10, color=INK)

    exploded = fig.add_axes((0.49, 0.28, 0.47, 0.58))
    draw(exploded, [(base, TEAL, (0, 0, 0)), (installed_lid(lid), CREAM, (0, 0, 27))]
         + [(shape, color, (0, 0, 16)) for _, shape, color in board])
    fig.text(0.56, 0.27, "02  EXPLODED", fontsize=11, weight="bold", color=INK)
    fig.text(0.56, 0.243, "10 mm below PCB for downward-facing headers", fontsize=10, color=INK)

    empty = fig.add_axes((0.02, 0.14, 0.48, 0.26))
    draw(empty, [(base, TEAL, (0, 0, 0))])
    fig.text(0.065, 0.12, "03  INSIDE THE BASE", fontsize=11, weight="bold", color=INK)
    fig.text(0.065, 0.093, "Four PCB supports · side and end locating stops", fontsize=10, color=INK)

    fig.text(0.56, 0.155, "PRINT FILES", fontsize=10, weight="bold", color=TEAL)
    fig.text(0.56, 0.123, "base.stl + lid.stl     |     enclosure.step", fontsize=12, color=INK)
    fig.text(0.56, 0.092, "Both STL parts sit flat at Z = 0 in printing orientation.", fontsize=10, color=INK)
    fig.text(0.055, 0.032, "CAD geometry preview. Board details are approximate; physical fit is untested.", fontsize=10, color="#697877")
    fig.savefig(OUT / "preview.png", dpi=170, facecolor=BG)
    plt.close(fig)
    print(OUT / "preview.png")


if __name__ == "__main__":
    main()
