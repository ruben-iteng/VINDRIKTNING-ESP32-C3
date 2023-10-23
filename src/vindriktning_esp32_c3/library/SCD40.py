from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.I2C import I2C


class SCD40(Module):
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
