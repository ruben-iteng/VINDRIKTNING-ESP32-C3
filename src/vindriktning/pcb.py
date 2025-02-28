# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import subprocess

import faebryk.library._F as F
from faebryk.exporters.pcb.kicad.transformer import (
    Font,
    Line,
    PCB_Transformer,
)
from faebryk.library.Net import Net
from faebryk.libs.geometry.basic import Geometry
from faebryk.libs.kicad.fileformats import (
    C_line,
    C_rect,
    C_stroke,
    C_wh,
    C_xy,
    C_xyr,
    E_fill,
)

logger = logging.getLogger(__name__)

"""
Here you can do PCB scripting.
E.g placing components, layer switching, mass renaming, etc.
"""


def transform_pcb(transformer: PCB_Transformer):
    # ----------------------------------------
    #               PCB outline
    # ----------------------------------------
    # right side of the outline
    outline_r = [
        (10, 0),
        (10, 5),
        (23, 5),
        (23, 25),
        (10, 25),
        (10, 57.5),
        (19, 57.5),
        (19, 65.5),
        (10, 65.5),
        (10, 72),
        (6.75, 72),
        (6.75, 75),
    ]
    # mirrored right side outline to left side
    outline_l = [(x * -1, y) for x, y in reversed(outline_r)]
    # add listst together (clockwise)
    outline_coordinates = outline_l + outline_r

    cutout_hole_coordinates = [
        (10, 9),
        (13, 9),
        (13, 16),
        (10, 16),
    ]

    set_outline(
        transformer,
        outline_coordinates,
        cutout_hole_coordinates,
        # outline_corner_radius_mm=0.5,
        # cutout_hole_corner_radius_mm=0.5,
        # TODO: fix corner radius
    )

    # ----------------------------------------
    #               Designators
    # ----------------------------------------
    transformer.hide_all_designators()


def set_outline(
    transformer: PCB_Transformer,
    outline_coordinates: list,
    cutout_hole_coordinates: list,
    outline_corner_radius_mm: float = 0.0,
    cutout_hole_corner_radius_mm: float = 0.0,
):
    # create line objects from coordinates
    outline_lines = []
    for coordinate in outline_coordinates:
        outline_lines.append(
            C_line(
                start=C_xy(coordinate[0], coordinate[1]),
                end=C_xy(
                    outline_coordinates[
                        (outline_coordinates.index(coordinate) + 1)
                        % len(outline_coordinates)
                    ][0],
                    outline_coordinates[
                        (outline_coordinates.index(coordinate) + 1)
                        % len(outline_coordinates)
                    ][1],
                ),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=transformer.gen_uuid(mark=True),
            )
        )
    transformer.set_pcb_outline_complex(
        outline_lines,
        remove_existing_outline=True,
        corner_radius_mm=outline_corner_radius_mm,
    )

    cutout_hole_lines = []
    for coordinate in cutout_hole_coordinates:
        cutout_hole_lines.append(
            Line(
                start=C_xy(coordinate[0], coordinate[1]),
                end=C_xy(
                    cutout_hole_coordinates[
                        (cutout_hole_coordinates.index(coordinate) + 1)
                        % len(cutout_hole_coordinates)
                    ][0],
                    cutout_hole_coordinates[
                        (cutout_hole_coordinates.index(coordinate) + 1)
                        % len(cutout_hole_coordinates)
                    ][1],
                ),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=transformer.gen_uuid(mark=True),
            ),
        )
    transformer.set_pcb_outline_complex(
        cutout_hole_lines,
        remove_existing_outline=False,
        corner_radius_mm=cutout_hole_corner_radius_mm,
    )
