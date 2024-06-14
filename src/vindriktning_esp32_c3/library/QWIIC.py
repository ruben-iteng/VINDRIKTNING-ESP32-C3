import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.util import times


class QWIIC(Module):
    """
    Sparkfun QWIIC connection spec. Also compatible with Adafruits STEMMA QT.
    Delivers 3.3V power + F.I2C over JST SH 1mm pitch 4 pin connectors
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            i2c = F.I2C()
            power = F.ElectricPower()
            # mount = times(2, Mechanical)
            mount = times(2, F.Electrical)

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.IFs.lv,
                    "2": x.power.IFs.hv,
                    "3": x.i2c.IFs.sda.IFs.signal,
                    "4": x.i2c.IFs.scl.IFs.signal,
                    "5": x.mount[0],
                    "6": x.mount[1],
                }
            )
        )

        # set constraints
        self.IFs.power.PARAMs.voltage.merge(F.Constant(3.3))
        # self.IFs.power.PARAMs.source_current.merge(F.Constant(226 * m))

        self.add_trait(F.has_designator_prefix_defined("J"))

        self.add_trait(F.has_datasheet_defined("https://www.sparkfun.com/qwiic"))
