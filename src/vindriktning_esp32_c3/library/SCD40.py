from dataclasses import dataclass, field

from faebryk.core.core import Module, Parameter
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Constant import Constant
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.has_esphome_config import (
    has_esphome_config,
    is_esphome_bus,
)
from faebryk.library.I2C import I2C
from faebryk.library.TBD import TBD
from faebryk.libs.units import k
from faebryk.libs.util import find


class SCD40(Module):
    @dataclass
    class _bh1750_esphome_config(has_esphome_config.impl()):
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
            i2c_cfg = i2c.get_trait(has_esphome_config).get_config()["i2c"][0]

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
                        "i2c_id": i2c_cfg["id"],
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

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "6": x.power.NODEs.lv,
                    "7": x.power.NODEs.hv,
                    "9": x.i2c.NODEs.scl.NODEs.signal,
                    "10": x.i2c.NODEs.sda.NODEs.signal,
                    "19": x.power.NODEs.hv,
                    "20": x.power.NODEs.lv,
                    "21": x.power.NODEs.lv,
                    "22": x.power.NODEs.lv,
                    "23": x.power.NODEs.lv,
                    "24": x.power.NODEs.lv,
                }
            )
        )

        self.add_trait(has_defined_type_description("U"))
        self.IFs.i2c.set_frequency(
            I2C.define_max_frequency_capability(I2C.SpeedMode.fast_speed)
        )

        # self.IFs.i2c.add_trait(is_esphome_bus.impl()())
        self.esphome = self._bh1750_esphome_config()
        self.add_trait(self.esphome)