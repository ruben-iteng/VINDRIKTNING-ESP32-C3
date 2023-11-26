from ast import Constant

from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.I2C import I2C
from faebryk.libs.units import m
from faebryk.libs.util import times


class QWIIC(Module):
    """
    Sparkfun QWIIC connection spec. Also compatible with Adafruits STEMMA QT.
    Delivers 3.3V power + I2C over JST SH 1mm pitch 4 pin connectors
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            i2c = I2C()
            power = ElectricPower()
            # mount = times(2, Mechanical)
            mount = times(2, Electrical)

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.NODEs.lv,
                    "2": x.power.NODEs.hv,
                    "3": x.i2c.NODEs.sda.NODEs.signal,
                    "4": x.i2c.NODEs.scl.NODEs.signal,
                    "5": x.mount[0],
                    "6": x.mount[1],
                }
            )
        )

        # set constraints
        self.IFs.power.add_constraint(
            ElectricPower.ConstraintVoltage(Constant(5)),
            ElectricPower.ConstraintCurrent(Constant(226 * m)),
        )

        self.add_trait(has_defined_type_description("J"))

        self.add_trait(has_datasheet_defined("https://www.sparkfun.com/qwiic"))
