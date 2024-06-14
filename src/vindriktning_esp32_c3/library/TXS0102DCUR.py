import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.util import times


class TXS0102DCUR(Module):
    """
    TXS0102 2-Bit Bidirectional Voltage-Level Translator for
    Open-Drain and Push-Pull Applications
    """

    class BidirectionalLevelShifter(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces
            class _IFs(Module.IFS()):
                low_side = F.ElectricLogic()
                high_side = F.ElectricLogic()

            self.IFs = _IFs(self)

            # connect all logic references
            ref = F.ElectricLogic.connect_all_module_references(self)
            self.add_trait(F.has_single_electric_reference_defined(ref))

            self.add_trait(F.can_bridge_defined(self.IFs.low_side, self.IFs.high_side))

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            low_voltage_power = F.ElectricPower()
            high_voltage_power = F.ElectricPower()
            n_oe = F.ElectricLogic()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            shifters = times(2, self.BidirectionalLevelShifter)

        self.NODEs = _NODEs(self)

        gnd = self.IFs.low_voltage_power.IFs.lv
        gnd.connect(self.IFs.high_voltage_power.IFs.lv)

        self.IFs.high_voltage_power.get_trait(F.can_be_decoupled).decouple()
        self.IFs.low_voltage_power.get_trait(F.can_be_decoupled).decouple()

        self.IFs.n_oe.connect_reference(self.IFs.low_voltage_power)

        # always enable level shifter
        if enabled:
            self.IFs.n_oe.set(False)

        for shifter in self.NODEs.shifters:
            shifter.IFs.high_side.IFs.reference.connect(self.IFs.high_voltage_power)
            shifter.IFs.low_side.IFs.reference.connect(self.IFs.low_voltage_power)

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": self.NODEs.shifters[1].IFs.high_side.IFs.signal,
                    "2": gnd,
                    "3": self.IFs.low_voltage_power.IFs.hv,
                    "4": self.NODEs.shifters[1].IFs.low_side.IFs.signal,
                    "5": self.NODEs.shifters[0].IFs.low_side.IFs.signal,
                    "6": self.IFs.n_oe.IFs.signal,
                    "7": self.IFs.high_voltage_power.IFs.hv,
                    "8": self.NODEs.shifters[0].IFs.high_side.IFs.signal,
                }
            )
        )

        self.add_trait(F.has_designator_prefix_defined("U"))

        self.add_trait(
            F.has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/1810292010_Texas-Instruments-TXS0102DCUR_C53434.pdf"
            )
        )
