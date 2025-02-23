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
        (19, 5),
        (19, 25),
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
    #           Graphical elements
    # ----------------------------------------
    # lines and graphics to indicate where points of the enclosure are touching the PCB
    transformer.insert_line(
        start=C_xy(10, 41),
        end=C_xy(-10, 41),
        width=0.2,
        layer="F.SilkS",
    )
    transformer.insert_line(
        start=C_xy(10, 47),
        end=C_xy(-10, 47),
        width=2,
        layer="F.SilkS",
    )
    transformer.insert_line(
        start=C_xy(19, 58),
        end=C_xy(-19, 58),
        width=0.2,
        layer="F.SilkS",
    )

    transformer.insert_geo(
        C_rect(
            start=C_xy(10, 0),
            end=C_xy(4.5, 1),
            stroke=C_stroke(0, C_stroke.E_type.solid),
            fill=E_fill.solid,
            layer="F.SilkS",
            uuid=transformer.gen_uuid(mark=True),
        )
    )

    # LED background
    transformer.insert_line(
        start=C_xy(0, 6.5),
        end=C_xy(0, 35.5),
        width=7,
        layer="B.SilkS",
    )

    # project name and version
    transformer.insert_text(
        text="Vindriktning",
        at=C_xyr(0, 55, 0),
        layer="F.SilkS",
        font=Font(size=C_wh(2, 2), thickness=0.15),
    )
    try:
        git_human_version = (
            subprocess.check_output(["git", "describe", "--always"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        logger.warning("Cannot get git project version")
        git_human_version = "Cannot get git project version"

    transformer.insert_text(
        text=git_human_version,
        at=C_xyr(0, 51, 0),
        layer="F.SilkS",
        font=Font(size=C_wh(1, 1), thickness=0.1),
    )

    transformer.insert_jlcpcb_qr(
        size=PCB_Transformer.JLCPBC_QR_Size.MEDIUM_8x8mm,
        center_at=C_xy(0, 47),
        layer="B.SilkS",
        number=False,
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
