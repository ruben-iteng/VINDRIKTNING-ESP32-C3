from dataclasses import dataclass, field

from faebryk.core.core import Module, Parameter
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.can_be_decoupled import can_be_decoupled
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.has_esphome_config import has_esphome_config
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.I2C import I2C
from faebryk.library.is_esphome_bus import is_esphome_bus
from faebryk.library.Resistor import Resistor
from faebryk.library.TBD import TBD


class SCD40(Module):
    """
    Sensirion SCD4x NIR CO2 sensor
    """

    @dataclass
    class _scd4x_esphome_config(has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, SCD40)

            i2c = is_esphome_bus.find_connected_bus(obj.IFs.i2c)

            return {
                "sensor": [
                    {
                        "platform": "scd4x",
                        "co2": {
                            "name": "CO2",
                        },
                        "temperature": {
                            "name": "Moving Temperature",
                        },
                        "humidity": {
                            "name": "Humidity",
                        },
                        "address": 0x62,
                        "i2c_id": i2c.get_trait(is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            i2c = I2C()

        self.IFs = _IFs(self)

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "6": self.IFs.power.IFs.lv,
                    "20": self.IFs.power.IFs.lv,
                    "21": self.IFs.power.IFs.lv,
                    "7": self.IFs.power.IFs.hv,
                    "19": self.IFs.power.IFs.hv,
                    "9": self.IFs.i2c.IFs.scl.IFs.signal,
                    "10": self.IFs.i2c.IFs.sda.IFs.signal,
                }
            )
        )
        # TODO: fix assign double footprint with this line
        # lcsc.attach_footprint(self, "C3659421")

        self.IFs.power.PARAMs.voltage.merge(Constant(3.3))

        self.IFs.i2c.terminate()
        self.IFs.power.get_trait(can_be_decoupled).decouple()

        self.add_trait(has_designator_prefix_defined("U"))
        self.IFs.i2c.PARAMs.frequency.merge(
            I2C.define_max_frequency_capability(I2C.SpeedMode.fast_speed)
        )
        self.add_trait(
            has_datasheet_defined(
                "https://sensirion.com/media/documents/48C4B7FB/64C134E7/Sensirion_SCD4x_Datasheet.pdf"
            )
        )

        self.IFs.i2c.add_trait(is_esphome_bus.impl()())
        self.esphome = self._scd4x_esphome_config()
        self.add_trait(self.esphome)

        # pcb layout
        self.add_trait(
            has_pcb_layout_defined(
                LayoutTypeHierarchy(
                    layouts=[
                        LayoutTypeHierarchy.Level(
                            mod_type=Resistor,
                            layout=LayoutExtrude(
                                base=has_pcb_position.Point(
                                    (
                                        -1.25,
                                        1.75,
                                        180,
                                        has_pcb_position.layer_type.NONE,
                                    )
                                ),
                                vector=(0, -1.25, 0),
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=Capacitor,
                            layout=LayoutExtrude(
                                base=has_pcb_position.Point(
                                    (
                                        -1.85,
                                        -6.5,
                                        180,
                                        has_pcb_position.layer_type.NONE,
                                    )
                                ),
                                vector=(0, 13, 0),
                            ),
                        ),
                    ],
                ),
            )
        )
