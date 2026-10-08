from printkit.manifest import Box, Drag, Model, Solid, dim, render


def make_model():
    model = Model(
        "demo",
        title="Demo",
        description="d",
        category="c",
        status="s",
        thumbnail="thumbnail.png",
        dimensions=(10, 20, 30),
        camera={
            "position": [1, 2, 3],
            "target": [0, 0, 0],
            "minDistance": 1,
            "maxDistance": 9,
            "views": [{"id": "top", "label": "Trên", "offset": [0, 0, 9]}],
        },
        grid={"size": 100, "divisions": 20},
        print_info={"summary": "x", "sections": []},
    )
    return model


def test_dim_geometry_and_label():
    line = dim(
        (-30, -42, 0),
        (30, -42, 0),
        offset=(0, -8, 0),
        name="Rộng",
        label_offset=(0, -4.8, 0),
    )
    assert line == {
        "a": [-30, -50, 0],
        "b": [30, -50, 0],
        "anchorA": [-30, -42, 0],
        "anchorB": [30, -42, 0],
        "label": "60 mm · Rộng",
        "labelOffset": [0, -4.8, 0],
    }


def test_dim_label_uses_length_and_prefix():
    assert (
        dim((0, 0, 11.8), (0, 0, 13.4), (0, 0, 0), "PCB dày")["label"]
        == "1.6 mm · PCB dày"
    )
    assert (
        dim((0, 0, 0), (18.5, 0, 0), (0, 0, 0), "Pin", prefix="Ø")["label"]
        == "Ø18.5 mm · Pin"
    )


def test_part_decorator_caches_build():
    model = make_model()
    calls = []

    @model.part("body", "Thân", color="#367c85", drag=Drag((0, 0, 1), 30))
    def body():
        calls.append(1)
        return object()

    assert body() is body() and len(calls) == 1
    assert model.parts[0].build is body
    assert model.parts[0].print_rotation == (0, 0, 0)


def test_render_parts_measurements_animations():
    model = make_model()

    @model.part("body", "Thân", color="#367c85", print_rotation=(0, 180, 0))
    def body():
        return None

    model.reference(
        "board",
        "Bo",
        [
            Box("pcb", (18, 22.5, 1.6), (0, 0, 12.6), "#214f55"),
            Solid("cell", None, "#87b483"),
        ],
        drag=Drag((0, 0, 1), 50),
    )
    model.measure(
        "case",
        "Vỏ",
        kind="case",
        follow="body",
        label_width=20,
        lines=[dim((0, 0, 0), (10, 0, 0), (0, -4, 0), "Rộng")],
        variants={"board": [dim((0, 0, 0), (9, 0, 0), (0, -4, 0), "Rộng")]},
    )
    model.animation(
        "open",
        "Mở",
        duration=10,
        open_pose={"body": (0, 0, 5)},
        tracks={"body": [(0, (0, 0, 0)), (0.5, (0, 0, 5)), (1, (0, 0, 0))]},
        camera=[(0, (0, 0, 0)), (1, (0, 0, 0))],
        measure_reveal=(0.3, 0.6),
    )
    data = render(
        model,
        {"body": ([1.0000000001, -0.0, 2], [0, 180, 0])},
        "../../model.schema.json",
    )

    assert data["$schema"] == "../../model.schema.json" and data["schemaVersion"] == 1
    assert data["downloads"] == {"bundle": "demo.zip", "step": "assembly.step"}
    body, board = data["parts"]
    assert body == {
        "id": "body",
        "label": "Thân",
        "kind": "print",
        "position": [1.0, 0.0, 2],
        "rotation": [0, 180, 0],
        "meshes": [{"src": "body.stl", "color": "#367c85"}],
    }
    assert board["kind"] == "reference" and board["position"] == [0, 0, 0]
    assert board["meshes"] == [
        {
            "primitive": "box",
            "size": [18, 22.5, 1.6],
            "position": [0, 0, 12.6],
            "color": "#214f55",
        },
        {"src": "reference/cell.stl", "color": "#87b483"},
    ]
    assert board["drag"] == {"axis": [0, 0, 1], "maxDistance": 50}
    measure = data["measurements"][0]
    assert (
        measure["color"] == "#efb96e"
        and measure["labelWidth"] == 20
        and "visibleWith" not in measure
    )
    assert measure["variants"][0]["whenHidden"] == "board"
    animation = data["animations"][0]
    assert animation["tracks"][0]["keyframes"][1] == {"time": 0.5, "value": [0, 0, 5]}
    assert animation["openPose"] == {"body": [0, 0, 5]} and animation[
        "measureReveal"
    ] == [0.3, 0.6]


def test_checks_register_in_order():
    model = make_model()

    @model.check("first")
    def first():
        return None

    @model.check("second")
    def second():
        return {"gap_mm": 1.0}

    assert [name for name, _ in model.checks] == ["first", "second"]


def test_pulse_rests_then_holds_then_returns():
    from printkit import pulse

    rest = (0, 0, 0)
    assert pulse((0, 0, 20)) == [
        (0, rest),
        (0.08, rest),
        (0.4, (0, 0, 20)),
        (0.72, (0, 0, 20)),
        (0.97, rest),
        (1, rest),
    ]
