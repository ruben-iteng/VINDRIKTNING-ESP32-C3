from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.libs.util import times
from faebryk.libs.units import n


class TXS0102DCUR(Module):
    """
    TXS0102 2-Bit Bidirectional Voltage-Level Translator for Open-Drain and Push-Pull Applications
    """

    class BidirectionalLevelShifter(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces
            class _IFs(Module.IFS()):
                low_side = ElectricLogic()
                high_side = ElectricLogic()

            self.IFs = _IFs(self)

            self.add_trait(can_bridge_defined(self.IFs.low_side, self.IFs.high_side))

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            low_voltage_power = ElectricPower()
            high_voltage_power = ElectricPower()
            n_oe = ElectricLogic()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            shifters = times(2, self.BidirectionalLevelShifter)
            decouple_caps = times(2, lambda: Capacitor(Constant(100 * n)))

        self.NODEs = _NODEs(self)

        I = self.IFs
        N = self.NODEs

        gnd = I.low_voltage_power.NODEs.lv
        gnd.connect(I.high_voltage_power.NODEs.lv)

        self.IFs.high_voltage_power.decouple(self.NODEs.decouple_caps[0])
        self.IFs.low_voltage_power.decouple(self.NODEs.decouple_caps[1])

        self.IFs.n_oe.connect_reference(self.IFs.low_voltage_power)

        # always enable level shifter
        if enabled:
            self.IFs.n_oe.set(False)

        for shifter in N.shifters:
            shifter.IFs.high_side.NODEs.reference.connect(I.high_voltage_power)
            shifter.IFs.low_side.NODEs.reference.connect(I.low_voltage_power)

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": N.shifters[1].IFs.high_side.NODEs.signal,
                    "2": gnd,
                    "3": I.low_voltage_power.NODEs.hv,
                    "4": N.shifters[1].IFs.low_side.NODEs.signal,
                    "5": N.shifters[0].IFs.low_side.NODEs.signal,
                    "6": I.n_oe.NODEs.signal,
                    "7": I.high_voltage_power.NODEs.hv,
                    "8": N.shifters[0].IFs.high_side.NODEs.signal,
                }
            )
        )

        self.add_trait(has_defined_type_description("U"))

        self.add_trait(
            has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/1810292010_Texas-Instruments-TXS0102DCUR_C53434.pdf"
            )
        )
