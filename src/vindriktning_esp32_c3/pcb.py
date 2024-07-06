# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from pathlib import Path
from typing import cast

from faebryk.core.graph import Graph
from faebryk.core.util import get_all_nodes
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.has_pcb_position_defined import has_pcb_position_defined
from faebryk.libs.app.pcb import apply_layouts, apply_routing
from faebryk.libs.kicad.pcb import PCB, Font, GR_Line, Symbol
from vindriktning_esp32_c3.app import SmartVindrikting
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.SCD40 import SCD40
from vindriktning_esp32_c3.library.USB_C_PSU_Vertical import USB_C_PSU_Vertical
from vindriktning_esp32_c3.modules.DigitalLED import DigitalLED
from vindriktning_esp32_c3.modules.IKEAVindriktningPMSensorInterface import (
    IKEAVindriktningPMSensorInterface,
)

logger = logging.getLogger(__name__)

"""
Here you can do PCB scripting.
E.g placing components, layer switching, mass renaming, etc.
"""


def transform_pcb(pcb_file: Path, graph: Graph, app: SmartVindrikting):
    logger.info("Load PCB")
    pcb = PCB.load(pcb_file)
    transformer = PCB_Transformer(pcb, graph, app)

    # ----------------------------------------
    #               PCB outline
    # ----------------------------------------
    # right side of the outline
    outline_r = [
        (0, 0),
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
        # (1.75, 75),
        # (0, 75),
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

    # create line objects from coordinates
    outline_lines = []
    for coordinate in outline_coordinates:
        outline_lines.append(
            GR_Line.factory(
                start=coordinate,
                end=outline_coordinates[
                    (outline_coordinates.index(coordinate) + 1)
                    % len(outline_coordinates)
                ],
                stroke=GR_Line.Stroke.factory(0.05, "default"),
                layer="Edge.Cuts",
                uuid=transformer.gen_uuid(mark=True),
            )
        )
    transformer.set_pcb_outline_complex(outline_lines, remove_existing_outline=True)

    cutout_hole_lines = []
    for coordinate in cutout_hole_coordinates:
        cutout_hole_lines.append(
            GR_Line.factory(
                start=coordinate,
                end=cutout_hole_coordinates[
                    (cutout_hole_coordinates.index(coordinate) + 1)
                    % len(cutout_hole_coordinates)
                ],
                stroke=GR_Line.Stroke.factory(0.05, "default"),
                layer="Edge.Cuts",
                uuid=transformer.gen_uuid(mark=True),
            ),
        )
    transformer.set_pcb_outline_complex(
        cutout_hole_lines, remove_existing_outline=False
    )

    # ----------------------------------------
    #               Fixes
    # ----------------------------------------
    footprints = [
        cmp.get_trait(PCB_Transformer.has_linked_kicad_footprint).get_fp()
        for cmp in get_all_nodes(transformer.app)
        if cmp.has_trait(PCB_Transformer.has_linked_kicad_footprint)
    ]
    # fix broken footprints
    for f in footprints:
        if f.name in [
            "lcsc:WIFIM-SMD_ESP32-C3-MINI-MINI-1U",
            "lcsc:WIFIM-SMD_ESP32-C3-MINI-1",
        ]:
            pad_candidate = [
                p for p in f.pads if p.name == "49" and Symbol("custom") in p.node
            ]
            if len(pad_candidate) < 1:
                continue
            pad = pad_candidate[0]
            logger.warning(f"Fixing footprint {f.name}")
            # 	(pad 49 smd custom (at -1.97 -1.98 0.00) (size 1.00 1.00) (layers F.Cu F.Paste F.Mask) # noqa E501
            #     (primitives
            #         (gr_poly
            #             (pts (xy -2.7 -2.1)(xy -2.1 -2.7)(xy -1.25 -2.7)(xy -1.25 -1.25)(xy -2.7 -1.25) # noqa E501
            #             )
            #             (width 0.1)
            #         )
            #     )
            # )
            ...
            pad.size = (1.45, 1.45)
            pad.get_prop("primitives")[0].delete()
            pad.node[pad.node.index(Symbol("custom"))] = Symbol("rect")

    # ----------------------------------------
    #               Designators
    # ----------------------------------------
    # move all reference designators to the same position
    for f in footprints:
        f.reference.layer = "F.SilkS" if f.layer.startswith("F") else "B.SilkS"
        rot = cast(tuple[float, float, float], f.at.coord)[2]
        f.reference.at.coord = (0, -1.25 if rot in [180, 270] else 1.25, rot)
        f.reference.font = Font.factory(size=(0.5, 0.5), thickness=0.1)  # 0.075)

    # ----------------------------------------
    #                   Layout
    # ----------------------------------------
    Point = has_pcb_position.Point
    L = has_pcb_position.layer_type

    app.add_trait(
        has_pcb_layout_defined(
            LayoutTypeHierarchy(
                layouts=[
                    LayoutTypeHierarchy.Level(
                        mod_type=ESP32_C3_MINI_1,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    -11,
                                    13,
                                    90,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=USB_C_PSU_Vertical,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    0,
                                    73,
                                    0,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=IKEAVindriktningPMSensorInterface,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    0,
                                    0,
                                    0,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=BH1750FVI_TR,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    0,
                                    7,
                                    180,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=HLK_LD2410B_P,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    16.25,
                                    61.5,
                                    0,
                                    L.NONE,  # TODO BOTTOM_LAYER
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=ME6211C33M5G_N,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    0,
                                    66,
                                    90,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=QWIIC,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    16,
                                    12.5,
                                    90,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=SCD40,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    3,
                                    11.5,
                                    0,
                                    L.NONE,
                                )
                            )
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=DigitalLED,
                        layout=LayoutAbsolute(
                            Point(
                                (
                                    0,
                                    11,
                                    0,
                                    L.BOTTOM_LAYER,
                                )
                            )
                        ),
                        # TODO: Fix children_layout
                        # children_layout=LayoutTypeHierarchy(
                        #    layouts=[
                        #        LayoutTypeHierarchy.Level(
                        #            mod_type=TXS0102DCUR,
                        #            layout=LayoutAbsolute(
                        #                Point(
                        #                    (
                        #                        -1.5,
                        #                        27.5,
                        #                        90,
                        #                        L.NONE,
                        #                    )
                        #                )
                        #            ),
                        #        ),
                        #    ]
                        # ),
                    ),
                ]
            )
        )
    )

    # set coordinate system
    app.add_trait(has_pcb_position_defined(Point((0, 0, 0, L.TOP_LAYER))))

    # apply layout
    apply_layouts(app)
    transformer.move_footprints()

    apply_routing(app, transformer)

    logger.info(f"Writing pcbfile {pcb_file}")
    pcb.dump(pcb_file)
