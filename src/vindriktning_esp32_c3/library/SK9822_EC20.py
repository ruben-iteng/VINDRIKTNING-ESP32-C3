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


class SK9822_EC20(Module):
    """
    SK9822 is a two-wire transmission channel three (RGB) driving intelligent control circuit and the light emitting circuit in one of the LED light source control. Products containing a signal decoding module, data buffer, a built-in constant current circuit and RC oscillator; CMOS, low voltage, low power consumption; 256 level grayscale PWM adjustment and 32 brightness adjustment; use the double output, Data and synchronization of the CLK signal, connected in series each wafer output action synchronization.
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            sdo = ElectricLogic()
            sdi = ElectricLogic()
            cko = ElectricLogic()
            ckl = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.sdo.NODEs.signal,
                    "2": x.power.NODEs.lv,
                    "3": x.sdi.NODEs.signal,
                    "4": x.ckl.NODEs.signal,
                    "5": x.power.NODEs.hv,
                    "6": x.cko.NODEs.signal,
                }
            )
        )

        self.add_trait(
            has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/2110250930_OPSCO-Optoelectronics-SK9822-EC20_C2909059.pdf"
            )
        )

        self.add_trait(has_defined_type_description("LED"))
