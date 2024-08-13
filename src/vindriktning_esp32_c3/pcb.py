# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import subprocess

import faebryk.library._F as F
from faebryk.core.util import get_all_nodes
from faebryk.exporters.pcb.kicad.transformer import (
    Font,
    Line,
    PCB_Transformer,
)
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.library.Fuse import Fuse
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.has_pcb_position_defined import has_pcb_position_defined
from faebryk.library.Net import Net
from faebryk.library.pf_533984002 import pf_533984002
from faebryk.library.Resistor import Resistor
from faebryk.libs.geometry.basic import Geometry
from faebryk.libs.kicad.fileformats import C_line, C_rect, C_stroke, C_wh, C_xy, C_xyr
from vindriktning_esp32_c3.app import SmartVindrikting
from vindriktning_esp32_c3.modules.DigitalLED import DigitalLED
from vindriktning_esp32_c3.modules.FanController import FanController
from vindriktning_esp32_c3.modules.IKEAVindriktningPMSensorInterface import (
    IKEAVindriktningPMSensorInterface,
)
from vindriktning_esp32_c3.modules.PCBMount import PCB_Mount

logger = logging.getLogger(__name__)

"""
Here you can do PCB scripting.
E.g placing components, layer switching, mass renaming, etc.
"""


def transform_pcb(transformer: PCB_Transformer):
    app = transformer.app
    assert isinstance(app, SmartVindrikting)

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
    #               Copper zones
    # ----------------------------------------
    copper_zone_offset = 1
    if True:
        # for _layer in transformer.get_copper_layers():
        transformer.insert_zone(
            net=transformer.get_net(Net.with_name("GND")),
            layers=["F.Cu", "B.Cu", "In1.Cu", "In2.Cu"],
            polygon=Geometry.rect_to_polygon(
                Geometry.bbox(
                    [Geometry.Point2D(coord) for coord in outline_coordinates],
                    copper_zone_offset,
                )
            ),
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
            fill=C_rect.E_fill.solid,
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
        front=True,
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
        front=True,
        font=Font(size=C_wh(1, 1), thickness=0.1),
    )

    # ----------------------------------------
    #               Designators
    # ----------------------------------------
    footprints = [
        cmp.get_trait(PCB_Transformer.has_linked_kicad_footprint).get_fp()
        for cmp in get_all_nodes(transformer.app)
        if cmp.has_trait(PCB_Transformer.has_linked_kicad_footprint)
    ]
    # move all reference designators to the same position
    for f in footprints:
        ref = f.propertys["Reference"]
        ref.layer = "F.SilkS" if f.layer.startswith("F") else "B.SilkS"
        ref.effects.font = Font(size=C_wh(0.5, 0.5), thickness=0.1)

    # ----------------------------------------
    #               Layout
    # ----------------------------------------
    apply_root_layout(app)

    # ----------------------------------------
    #               Routing
    # ----------------------------------------
    apply_routing(transformer)


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


def apply_routing(transformer: PCB_Transformer):
    for node in get_all_nodes(transformer.app):
        if isinstance(node, F.Capacitor):
            node.add_trait(
                F.has_pcb_routing_strategy_greedy_direct_line(
                    F.has_pcb_routing_strategy_greedy_direct_line.Topology.DIRECT
                )
            )


def apply_root_layout(app: SmartVindrikting):
    Point = has_pcb_position.Point
    L = has_pcb_position.layer_type
    LVL = LayoutTypeHierarchy.Level

    # manual placement
    layouts = [
        LVL(
            mod_type=F.ESP32_C3_MINI_1_Reference_Design,
            layout=LayoutAbsolute(Point((0, 0, 0, L.NONE))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.ESP32_C3_MINI_1,
                        layout=LayoutAbsolute(Point((-11, 13, 90, L.TOP_LAYER))),
                    ),
                    LVL(
                        mod_type=F.Button,
                        layout=LayoutExtrude(
                            base=Point((13.5, 61.5, 0, L.TOP_LAYER)),
                            vector=(-27, 0, 90),
                        ),
                    ),
                ]
            ),
        ),
        LVL(
            mod_type=F.USB_C_PSU_Vertical,
            layout=LayoutAbsolute(Point((0, 73, 0, L.TOP_LAYER))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.USB_Type_C_Receptacle_14_pin_Vertical,
                        layout=LayoutAbsolute(Point((0, 0.2, 0, L.NONE))),
                    ),
                    LVL(
                        mod_type=F.USB2_0_ESD_Protection,
                        layout=LayoutAbsolute(Point((-8, -11.5, 0, L.NONE))),
                    ),
                    LVL(
                        mod_type=Fuse,
                        layout=LayoutAbsolute(Point((2.75, -4.5, 90, L.NONE))),
                    ),
                    LVL(
                        mod_type=F.Capacitor,
                        layout=LayoutAbsolute(Point((-2.5, -4.5, 90, L.NONE))),
                    ),
                    LVL(
                        mod_type=Resistor,
                        layout=LayoutExtrude(
                            base=Point((-1.25, -4.5, 90, L.NONE)),
                            vector=(0, 1.25, 0),
                        ),
                    ),
                ]
            ),
        ),
        LVL(
            mod_type=IKEAVindriktningPMSensorInterface,
            layout=LayoutAbsolute(Point((0, 0, 0, L.TOP_LAYER))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=FanController,
                        layout=LayoutAbsolute(Point((2.5, 30, 0, L.NONE))),
                        children_layout=LayoutTypeHierarchy(
                            layouts=[
                                LVL(
                                    mod_type=F.PoweredLED,
                                    layout=LayoutAbsolute(Point((5.5, 0, 90, L.NONE))),
                                    children_layout=LayoutTypeHierarchy(
                                        layouts=[
                                            LVL(
                                                mod_type=F.LED,
                                                layout=LayoutAbsolute(
                                                    Point((0, 0, 0, L.NONE))
                                                ),
                                            ),
                                            LVL(
                                                mod_type=F.Resistor,
                                                layout=LayoutAbsolute(
                                                    Point((-3, 0, 90, L.NONE))
                                                ),
                                            ),
                                        ]
                                    ),
                                ),
                                LVL(
                                    mod_type=F.PowerSwitchMOSFET,
                                    layout=LayoutAbsolute(Point((0, 0, 0, L.NONE))),
                                    children_layout=LayoutTypeHierarchy(
                                        layouts=[
                                            LVL(
                                                mod_type=F.Resistor,
                                                layout=LayoutAbsolute(
                                                    Point((0, 2.5, 180, L.NONE))
                                                ),
                                            ),
                                            LVL(
                                                mod_type=F.MOSFET,
                                                layout=LayoutAbsolute(
                                                    Point((0, 0, 0, L.NONE))
                                                ),
                                            ),
                                        ]
                                    ),
                                ),
                                LVL(
                                    mod_type=F.Diode,
                                    layout=LayoutAbsolute(Point((0, -3, 180, L.NONE))),
                                ),
                            ]
                        ),
                    ),
                    LVL(
                        mod_type=pf_533984002,
                        layout=LayoutAbsolute(Point((2, 23, 180, L.NONE))),
                    ),
                    LVL(
                        mod_type=F.TXS0102DCUR,
                        layout=LayoutAbsolute(Point((0, 2.5, 90, L.NONE))),
                    ),
                    LVL(
                        mod_type=F.B4B_ZR_SM4_TF,
                        layout=LayoutAbsolute(Point((13, 21, 180, L.NONE))),
                    ),
                ]
            ),
        ),
        LVL(
            mod_type=F.BH1750FVI_TR,
            layout=LayoutAbsolute(Point((0, 7, 180, L.BOTTOM_LAYER))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.Resistor,
                        layout=LayoutExtrude(
                            base=Point((-3, 1, 180, L.NONE)),
                            vector=(0, 2, 0),
                        ),
                    ),
                    LVL(
                        mod_type=F.Capacitor,
                        layout=LayoutAbsolute(pos=Point((0, 1.75, 0, L.NONE))),
                    ),
                ],
            ),
        ),
        LVL(
            mod_type=F.HLK_LD2410B_P,
            layout=LayoutAbsolute(Point((16.25, 61.5, 0, L.BOTTOM_LAYER))),
        ),
        LVL(
            mod_type=F.ME6211C33M5G_N,
            layout=LayoutExtrude(
                base=Point((-1, 61.5, 90, L.TOP_LAYER)), vector=(0, 6, 0)
            ),
        ),
        LVL(
            mod_type=F.QWIIC,
            layout=LayoutAbsolute(Point((16, 12.5, 90, L.TOP_LAYER))),
        ),
        LVL(
            mod_type=F.Fuse,
            layout=LayoutAbsolute(Point((15, 7.5, 180, L.TOP_LAYER))),
        ),
        LVL(
            mod_type=F.SCD40,
            layout=LayoutAbsolute(Point((3, 11.5, 0, L.TOP_LAYER))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.Resistor,
                        layout=LayoutExtrude(
                            base=Point((1.25, 7, 90, L.NONE)),
                            vector=(0, 1.25, 180),
                        ),
                    ),
                    LVL(
                        mod_type=F.Capacitor,
                        layout=LayoutExtrude(
                            base=Point((-1.85, -6.5, 180, L.NONE)),
                            vector=(0, 13, 0),
                        ),
                    ),
                ],
            ),
        ),
        LVL(
            mod_type=DigitalLED,
            layout=LayoutAbsolute(Point((0, 11, 0, L.NONE))),
            children_layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.TXS0102DCUR,
                        layout=LayoutAbsolute(Point((-1.5, 17, 0, L.TOP_LAYER))),
                    ),
                    LVL(
                        mod_type=DigitalLED.DecoupledDigitalLED,
                        layout=LayoutExtrude(
                            base=Point(
                                (
                                    0,
                                    30.5
                                    - (
                                        30.5
                                        / 5
                                        * len(app.NODEs.mcu_pcb.NODEs.leds.NODEs.leds)
                                    ),
                                    0,
                                    L.BOTTOM_LAYER,
                                )
                            ),
                            vector=(
                                0,
                                30.5 / 5,
                                0,
                            ),
                        ),
                        children_layout=LayoutTypeHierarchy(
                            layouts=[
                                LVL(
                                    mod_type=F.Capacitor,
                                    layout=LayoutAbsolute(
                                        Point((1.5, 3, 270, L.NONE)),
                                    ),
                                ),
                                LVL(
                                    mod_type=F.XL_3528RGBW_WS2812B,
                                    layout=LayoutAbsolute(Point((0, 0, 180, L.NONE))),
                                ),
                            ]
                        ),
                    ),
                ]
            ),
        ),
        LVL(
            mod_type=PCB_Mount,
            layout=LayoutAbsolute(Point((0, 0, 0, L.TOP_LAYER))),
        ),
    ]

    app.add_trait(has_pcb_layout_defined(LayoutTypeHierarchy(layouts)))

    # set coordinate system
    app.add_trait(has_pcb_position_defined(Point((0, 0, 0, L.NONE))))
