from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.libs.util import times
from faebryk.libs.library import L
from faebryk.libs.units import P

LT = has_pcb_position.layer_type
LVL = LayoutTypeHierarchy.Level
Point = has_pcb_position.Point


class LEDString(Module):
    """
    Create a string of WS2812B RGBW LEDs with optional signal level translator
    """

    class _esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj(LEDString)

            gpio = F.is_esphome_bus.find_connected_bus(obj.data_in)

            return {
                "sensor": [
                    {
                        "platform": "esp32_rmt_led_strip",
                        "name": "F.LED string",
                        "rgb_order": "GRB",
                        "pin": gpio.get_trait(F.is_esphome_bus).get_bus_id(),
                        "num_leds": len(obj.leds),
                        "rmt_channel": 0,
                        "chipset": "SK6812",
                        "is_rgbw": False,
                        "max_refresh_rate": obj.max_refresh_rate,
                    }
                ]
            }

    esphome_config: _esphome_config

    class DecoupledDigitalLED(Module):
        def __init__(self, led_class):
            super().__init__()
            self._led_class = led_class

        data_in: F.ElectricLogic
        data_out: F.ElectricLogic
        power: F.ElectricPower

        @L.rt_field
        def led(self):
            return self._led_class()

        @L.rt_field
        def single_electric_reference(self):
            return F.has_single_electric_reference_defined(
                F.ElectricLogic.connect_all_module_references(self)
            )

        @L.rt_field
        def can_bridge(self):
            return F.can_bridge_defined(self.data_in, self.data_out)

        def __preinit__(self):
            self.data_in.connect_via(self.led, self.data_out)

            self.power.connect(self.led.power)

            decoupling_cap = self.power.decoupled.decouple(
                owner=self, count=1
            ).capacitors[0]
            decoupling_cap.capacitance.constrain_subset(
                L.Range.from_center_rel(100 * P.nF, 0.1)
            )
            decoupling_cap.add(F.has_package(F.has_package.Package.C0402))

            # ------------------------------------
            #            pcb layout
            # ------------------------------------
            self.add(
                F.has_pcb_layout_defined(
                    layout=LayoutTypeHierarchy(
                        layouts=[
                            LVL(
                                mod_type=type(self._led_class()),
                                layout=LayoutAbsolute(Point((0, 0, 180, LT.NONE))),
                            ),
                            LVL(
                                # TODO: this does not work, decoupling_cap is part of power.decoupled
                                mod_type=F.Capacitor,
                                layout=LayoutAbsolute(
                                    Point((-0.95, 2, 0, LT.NONE)),
                                ),
                            ),
                        ],
                    ),
                ),
            )

    def __init__(self, pixels: int = 5, buffered: bool = True):
        super().__init__()
        self._pixels = pixels
        self._buffered = buffered

    data_in: F.ElectricLogic
    power: F.ElectricPower
    power_data: F.ElectricPower
    max_refresh_rate = L.p_field(units=P.hertz)

    @L.rt_field
    def leds(self):
        return times(
            self._pixels, lambda: self.DecoupledDigitalLED(F.XL_3528RGBW_WS2812B)
        )

    def __preinit__(self):
        # connect power
        for led in self.leds:
            led.power.connect(self.power)
            led.led.add(  # TODO: move to library
                F.has_explicit_part.by_mfr(
                    mfr="XINGLIGHT",
                    partno="XL-3528RGBW-WS2812B",
                )
            )

        if self._buffered:
            buffer = self.add(F.TXS0102DCUR())

            self.data_in.connect(buffer.shifters[0].io_a)
            buffer.shifters[0].io_b.connect_via(self.leds)

            buffer.n_oe.set(True)
            buffer.voltage_a_power.connect(self.power_data)
            buffer.voltage_b_power.connect(self.power)
            ref = self.power_data
        else:
            self.power_data.connect(self.power)
            self.data_in.connect_via(self.leds)
            ref = self.power

        self.data_in.reference.connect(ref)

        # ------------------------------------
        #            pcb layout
        # ------------------------------------
        self.add(
            F.has_pcb_layout_defined(
                layout=LayoutTypeHierarchy(
                    layouts=[
                        LVL(
                            mod_type=F.TXS0102DCUR,
                            layout=LayoutAbsolute(Point((-1.5, 19, 0, LT.TOP_LAYER))),
                        ),
                        LVL(
                            mod_type=self.DecoupledDigitalLED,
                            layout=LayoutExtrude(
                                base=Point(
                                    (
                                        0,
                                        30.5 - (30.5 / 5 * len(self.leds)),
                                        0,
                                        LT.BOTTOM_LAYER,
                                    )
                                ),
                                vector=(
                                    0,
                                    30.5 / 5,
                                    0,
                                ),
                            ),
                        ),
                    ]
                ),
            ),
        )
