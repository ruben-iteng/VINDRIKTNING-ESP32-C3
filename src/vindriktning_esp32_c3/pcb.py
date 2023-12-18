import logging
from typing import TypeVar, cast

from faebryk.core.core import Module, Node
from faebryk.core.util import get_all_nodes
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Diode import Diode
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.has_pcb_position_defined import has_pcb_position_defined
from faebryk.library.LED import LED
from faebryk.library.LEDIndicator import PowerSwitch
from faebryk.library.MOSFET import MOSFET
from faebryk.library.PoweredLED import PoweredLED
from faebryk.library.Resistor import Resistor
from faebryk.library.Switch import _TSwitch
from faebryk.libs.kicad.pcb import Symbol
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.Mounting_Hole import Mounting_Hole
from vindriktning_esp32_c3.library.pf_74AHCT2G125 import pf_74AHCT2G125
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.USB_C_PSU_Vertical import USB_C_PSU_Vertical
from vindriktning_esp32_c3.library.USB_Type_C_Receptacle_14_pin_Vertical import (
    USB_Type_C_Receptacle_14_pin_Vertical,
)
from vindriktning_esp32_c3.library.USBLC6_2P6 import USBLC6_2P6
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B
from vindriktning_esp32_c3.vindriktning_esp32_c3_base import (
    TXS0102DCUR,
    CO2_Sensor,
    Fan_Controller,
    Ikea_Vindriktning_PM_Sensor,
    LevelBuffer,
    PCB_Mount,
    Vindriktning_ESP32_C3,
    digitalLED,
)

# logging settings
logger = logging.getLogger(__name__)

PERMANENT = False

T = TypeVar("T", bound=Node)


def get_nodes_with_type(nodes: list[Node], node_type: type[T]) -> list[T]:
    return [n for n in nodes if isinstance(n, node_type)]


class has_pcb_position_defined_relative(has_pcb_position.impl()):
    def __init__(self, position_relative: has_pcb_position.Point, to: Module) -> None:
        super().__init__()
        self.position_relative = position_relative
        self.to = to

    def get_position(self) -> has_pcb_position.Point:
        return PCB_Transformer.Geometry.abs_pos(
            self.to.get_trait(has_pcb_position).get_position(), self.position_relative
        )


class has_pcb_position_defined_relative_to_parent(has_pcb_position.impl()):
    def __init__(self, position_relative: has_pcb_position.Point):
        super().__init__()
        self.position_relative = position_relative

    def get_position(self) -> has_pcb_position.Point:
        for parent, _ in reversed(self.get_obj().get_hierarchy()[:-1]):
            if parent.has_trait(has_pcb_position):
                pos = parent.get_trait(has_pcb_position).get_position()
                logger.info(
                    f"Found parent position for: {self.get_obj().get_full_name()}: {pos} [{parent.get_full_name()}]"
                )
                return PCB_Transformer.Geometry.abs_pos(
                    pos,
                    self.position_relative,
                )
        raise Exception(
            f"Component of type {type(self.get_obj())} with relative to parent position has no (valid) parent"
        )


def move_footprints(transformer: PCB_Transformer):
    # position modules with defined positions
    pos_mods: set[Module] = {
        gif.node
        for gif in transformer.graph.G.nodes
        if gif.node.has_trait(has_pcb_position)
        and gif.node.has_trait(transformer.has_linked_kicad_footprint)
    }
    logger.info(f"Positioning {len(pos_mods)} footprints")

    for module in pos_mods:
        fp = module.get_trait(transformer.has_linked_kicad_footprint).get_fp()
        coord = module.get_trait(has_pcb_position).get_position()
        layer_name = {
            has_pcb_position.layer_type.TOP_LAYER: "F.Cu",
            has_pcb_position.layer_type.BOTTOM_LAYER: "B.Cu",
        }

        if coord[3] == has_pcb_position.layer_type.NONE:
            raise Exception(f"Component {module}({fp.name}) has no layer defined")

        logger.info(f"Placing {fp.name} at {coord} layer {layer_name[coord[3]]}")
        transformer.move_fp(fp, coord[:3], layer_name[coord[3]])


def transform_pcb(transformer: PCB_Transformer):
    FONT_SCALE = 8
    FONT = (1 / FONT_SCALE, 1 / FONT_SCALE, 0.15 / FONT_SCALE)
    PLACE_VIAS = False

    footprints = [
        cmp.get_trait(PCB_Transformer.has_linked_kicad_footprint).get_fp()
        for cmp in get_all_nodes(transformer.app)
        if cmp.has_trait(PCB_Transformer.has_linked_kicad_footprint)
    ]

    assert isinstance(transformer.app, Vindriktning_ESP32_C3)
    app: Vindriktning_ESP32_C3 = transformer.app

    # create pcb edge cut
    # transformer.set_dimensions_rectangle(
    #    height_mm=75, width_mm=20, origin_x_mm=-10, origin_y_mm=0
    # )

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
        (0, 75),
    ]
    # mirrored right side outline to left side
    outline_l = [(x * -1, y) for x, y in reversed(outline_r)]
    hole = [
        (10, 9),
        (13, 9),
        (13, 16),
        (10, 16),
    ]
    # add listst together (clockwise)
    outline = outline_r + outline_l

    transformer.set_dimensions_complex(
        points=outline,
        origin_x_mm=0,
        origin_y_mm=0,
    )

    transformer.set_dimensions_complex(
        points=hole,
        origin_x_mm=0,
        origin_y_mm=0,
        remove_existing_outline=False,
    )

    # positioning -------------------------------------------------------------
    LT = has_pcb_position.layer_type

    def set_parent_rel_pos(node: Node, pos: has_pcb_position.Point):
        node.add_trait(has_pcb_position_defined_relative_to_parent(pos))

    def set_abs_pos(node: Node, pos: has_pcb_position.Point):
        node.add_trait(has_pcb_position_defined(pos))

    def set_simple_layout(node: Node, layout: dict, first=True):
        nodes = get_all_nodes(node)
        if not any([isinstance(node, t) for t in layout.keys()]):
            for child in nodes:
                set_simple_layout(child, layout, first)
            return

        pos, sub_layout = [val for key, val in layout.items() if isinstance(node, key)][
            0
        ]
        if first:
            set_abs_pos(node, pos)
        else:
            set_parent_rel_pos(node, pos)

        for child in nodes:
            set_simple_layout(child, sub_layout, False)

    nodes = get_all_nodes(app)

    # layouts ==================================================================
    # set default to inherit position from parent
    set_abs_pos(app, (0, 0, 0, LT.TOP_LAYER))
    for cmp in nodes:
        set_parent_rel_pos(cmp, (0, 0, 0, LT.NONE))

    simple_layout = {
        ME6211C33M5G_N: ((0, 66, 90, LT.TOP_LAYER), {}),
        HLK_LD2410B_P: ((16.25, 61.5, 0, LT.BOTTOM_LAYER), {}),
        BH1750FVI_TR: (
            (0, 7, 180, LT.BOTTOM_LAYER),
            {
                # Resistor: ((-1.25, -1.75, 0, LT.NONE), {}),
                # Capacitor: ((1.25, -1.75, 0, LT.NONE), {}),
            },
        ),
        ESP32_C3_MINI_1_VIND: (
            (-11, 13, 90, LT.TOP_LAYER),
            {
                # Capacitor: ((-1.75, 7.75, 270, LT.NONE), {}),
            },
        ),
        QWIIC: (
            (16, 12.5, 90, LT.TOP_LAYER),
            {},
        ),
        CO2_Sensor: (
            (3, 11.5, 0, LT.TOP_LAYER),
            {
                # Capacitor: ((0, 4, 0, LT.NONE), {}),
            },
        ),
        USB_C_PSU_Vertical: (
            (0, 73, 0, LT.TOP_LAYER),
            {
                USBLC6_2P6: ((-5, -8.5, 0, LT.NONE), {}),
                Capacitor: ((0, 0, 0, LT.NONE), {}),
                USB_Type_C_Receptacle_14_pin_Vertical: (
                    (0, 0.2, 0, LT.NONE),
                    {},
                ),
            },
        ),
        Ikea_Vindriktning_PM_Sensor: (
            (0, 0, 0, LT.TOP_LAYER),
            {
                # TODO cluster in module
                # PM
                Ikea_Vindriktning_PM_Sensor.PM1006_Connector: (
                    (-13, -21, 180, LT.NONE),
                    {
                        B4B_ZR_SM4_TF: ((0, 0, 0, LT.NONE), {}),
                    },
                ),
                Ikea_Vindriktning_PM_Sensor.UART_Shifter: (
                    (-2.5, 0, 90, LT.NONE),
                    {
                        TXS0102DCUR: (
                            (0, 0, 0, LT.NONE),
                            {
                                # Capacitor: ((0, 0, 0, LT.NONE), {}),
                            },
                        ),
                    },
                ),
                # Fan
                Ikea_Vindriktning_PM_Sensor.Fan_Connector: (
                    (-2, -23, 180, LT.NONE),
                    {
                        pf_533984002: ((0, 0, 0, LT.NONE), {}),
                    },
                ),
                Fan_Controller: (
                    (2.5, 27.5, 0, LT.NONE),
                    {
                        PoweredLED: (
                            (0, 5.5, 90, LT.NONE),
                            {
                                LED: ((0, 0, 180, LT.NONE), {}),
                                Resistor: ((0, 3, 270, LT.NONE), {}),
                            },
                        ),
                        PowerSwitch: (
                            (0, 0, 0, LT.NONE),
                            {
                                MOSFET: ((0, 0, 0, LT.NONE), {}),
                                Resistor: ((0, 2.5, 0, LT.NONE), {}),
                            },
                        ),
                        Diode: (
                            (0, 3, 90, LT.NONE),
                            {},
                        ),
                    },
                ),
            },
        ),
        LevelBuffer: (
            (0, 0, 0, LT.TOP_LAYER),
            {
                pf_74AHCT2G125: ((0, 0, 0, LT.NONE), {}),
                Capacitor: ((0, -2.5, 90, LT.NONE), {}),
            },
        ),
        digitalLED: (
            (0, 11, 0, LT.NONE),
            {
                XL_3528RGBW_WS2812B: ((0, 0, 0, LT.NONE), {}),
                Capacitor: ((0, 2.5, 0, LT.NONE), {}),
            },
        ),
        _TSwitch: ((0, 0, 0, LT.NONE), {}),
        PCB_Mount: (
            (0, 0, 0, LT.TOP_LAYER),
            {
                Mounting_Hole: ((0, 0, 0, LT.NONE), {}),
            },
        ),
    }

    set_simple_layout(transformer.app, simple_layout)

    # non-simple layouts
    for cmp in nodes:
        # distribute for each digitalLED the pixel (and drivers thereof) along a line
        if isinstance(cmp, digitalLED):
            set_abs_pos(cmp.NODEs.buffer, (-1.5, 27.5, 90, LT.TOP_LAYER))
            for led_i, led in enumerate(cmp.NODEs.leds):
                set_parent_rel_pos(led, (0, 30.5 / 5 * led_i, 0, LT.BOTTOM_LAYER))
        if isinstance(cmp, ME6211C33M5G_N):
            for cap_i, cap in enumerate(cmp.NODEs.decoupling_caps):
                set_parent_rel_pos(cap, (0, -3 if cap_i == 1 else 3, 0, LT.NONE))
        if isinstance(cmp, Ikea_Vindriktning_PM_Sensor):
            # set_parent_rel_pos(cmp.NODEs.pm_sensor_buffer, (0, 2.5, 0, LT.NONE))
            for cap_i, cap in enumerate(
                cmp.NODEs.pm_sensor_buffer.NODEs.buffer.NODEs.decouple_caps
            ):
                set_parent_rel_pos(cap, (0, -3 if cap_i == 0 else 3, 0, LT.NONE))
            for res_i, res in enumerate(
                cmp.NODEs.uart_bus_voltage_dropper.NODEs.voltage_drop_resistors
            ):
                set_parent_rel_pos(res, (5, 1.75 if res_i == 0 else 3, 0, LT.NONE))
        if isinstance(cmp, PCB_Mount):
            for hole_i, hole in enumerate(cmp.NODEs.screw_holes):
                if hole_i == 0:
                    set_abs_pos(hole, (-6.5, 2.5, 0, LT.TOP_LAYER))
                else:
                    set_abs_pos(
                        hole, (7.5 if hole_i == 1 else -7.5, 69.5, 0, LT.TOP_LAYER)
                    )
        if isinstance(cmp, USB_C_PSU_Vertical):
            for res_i, res in enumerate(cmp.NODEs.configuration_resistors):
                set_parent_rel_pos(
                    res,
                    (
                        -2.5 if res_i == 1 else -2.5,
                        -4.5 if res_i == 1 else 4.5,
                        0 if res_i == 1 else 180,
                        LT.NONE,
                    ),
                )
            set_parent_rel_pos(
                cmp.NODEs.gnd_capacitor,
                (0, -5.5, 90, LT.NONE),
            )
            set_parent_rel_pos(
                cmp.NODEs.gnd_resistor,
                (0, 5.5, 90, LT.NONE),
            )
            set_parent_rel_pos(
                cmp.NODEs.esd_capacitor,
                (-9.5, 7.5, 270, LT.NONE),
            )
        if isinstance(cmp, CO2_Sensor):
            for res_i, res in enumerate(cmp.NODEs.pullup_resistors):
                set_parent_rel_pos(res, (-7, 2.5 if res_i == 1 else 1.25, 90, LT.NONE))
            for cap_i, cap in enumerate(cmp.NODEs.decoupling_caps):
                set_parent_rel_pos(
                    cap,
                    (
                        1.85 if cap_i == 1 else 1.85,
                        -6.5 if cap_i == 1 else 6.5,
                        180 if cap_i == 1 else 180,
                        LT.NONE,
                    ),
                )
        if isinstance(cmp, BH1750FVI_TR):
            set_parent_rel_pos(cmp.NODEs.decoupling_cap, (0, 1.75, 0, LT.NONE))
            set_parent_rel_pos(cmp.NODEs.dvi_capacitor, (1.25, -1.75, 0, LT.NONE))
            set_parent_rel_pos(cmp.NODEs.dvi_resistor, (-1.25, -1.75, 0, LT.NONE))
            for res_i, res in enumerate(cmp.NODEs.i2c_termination_resistors):
                set_abs_pos(
                    res,
                    (
                        -12.25,
                        12 if res_i == 0 else 13.25,
                        180,
                        LT.BOTTOM_LAYER,
                    ),
                )
        if isinstance(cmp, ESP32_C3_MINI_1_VIND):
            set_parent_rel_pos(cmp.NODEs.en_rc_resesitor, (-9.5, 1.6, 0, LT.NONE))
            set_parent_rel_pos(cmp.NODEs.en_rc_capacitor, (9.5, -3.1, 180, LT.NONE))
            set_parent_rel_pos(cmp.NODEs.boot_resistors[1], (-9.5, -0.8, 0, LT.NONE))
            set_parent_rel_pos(cmp.NODEs.boot_resistors[0], (2.75, 6.75, 0, LT.NONE))
            for cap_i, cap in enumerate(cmp.NODEs.pwr_3v3_decoupling_caps):
                set_parent_rel_pos(
                    cap,
                    (
                        3.75 if cap_i == 1 else 4,
                        -9 if cap_i == 1 else -10.75,
                        90,
                        LT.NONE,
                    ),
                )
            for switch_i, switch in enumerate(cmp.NODEs.switches):
                set_abs_pos(
                    cmp.NODEs.switches[switch_i],
                    (
                        13.5 if switch_i == 0 else -13.5,
                        61.5,
                        90 if switch_i == 0 else 270,
                        LT.TOP_LAYER,
                    ),
                )
                set_abs_pos(
                    cmp.NODEs.debounce_capacitors[switch_i],
                    (10.75 if switch_i == 0 else -10.75, 60, 90, LT.TOP_LAYER),
                )
                set_abs_pos(
                    cmp.NODEs.debounce_resistors[switch_i],
                    (10.75 if switch_i == 0 else -10.75, 63, 270, LT.TOP_LAYER),
                )

    # ==========================================================================
    # --------------------------------------------------------------------------
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
            # 	(pad 49 smd custom (at -1.97 -1.98 0.00) (size 1.00 1.00) (layers F.Cu F.Paste F.Mask)
            #     (primitives
            #         (gr_poly
            #             (pts (xy -2.7 -2.1)(xy -2.1 -2.7)(xy -1.25 -2.7)(xy -1.25 -1.25)(xy -2.7 -1.25)
            #             )
            #             (width 0.1)
            #         )
            #     )
            # )
            ...
            pad.size = (1.45, 1.45)
            pad.get_prop("primitives")[0].delete()
            pad.node[pad.node.index(Symbol("custom"))] = Symbol("rect")

    # --------------------------------------------------------------------------
    # rename, resize, relayer text
    for f in footprints:
        # ref
        f.reference.layer = "F.SilkS" if f.layer.startswith("F") else "B.SilkS"
        f.reference.at.coord = (0, 0, 0)
        f.reference.font = (0.5, 0.5, 0.1)  # 0.075)

    # user
    # name = f.reference.text.split(".")
    # user_text = next(filter(lambda x: not x.text.startswith("FBRK:"), f.user_text))
    # user_text.text = f"{name[1]}.{name[-1].split('[')[0]}"
    # user_text.layer = "F.Silkscreen"
    # user_text.layer = "User.7"
    # user_text.font = FONT

    # reposition silkscreen text
    for f in footprints:
        assert len(f.at.coord) > 2
        rot = cast(tuple[float, float, float], f.at.coord)[2]
        # if f.name in [*MOSFET_FPS, RESISTOR_FP, LED_FP]:
        # user_text = next(filter(lambda x: not x.text.startswith("FBRK:"), f.user_text))
        user_text = (
            f.reference
        )  # next(filter(lambda x: not x.text.startswith("FBRK:"), f.user_text))
        user_text.at.coord = (0, -1.25 if rot in [180, 270] else 1.25, rot)

    move_footprints(transformer)
