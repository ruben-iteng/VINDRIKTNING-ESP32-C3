import faebryk.library._F as F
from faebryk.core.core import Module


class SK9822_EC20(Module):
    """
    SK9822 is a two-wire transmission channel three
    (RGB) driving intelligent control circuit and
    the light emitting circuit in one of the LED light
    source control. Products containing a signal
    decoding module, data buffer, a built-in Constant
    current circuit and RC oscillator; CMOS, low
    voltage, low power consumption; 256 level grayscale
    PWM adjustment and 32 brightness adjustment;
    use the double output, Data and synchronization of
    the CLK signal, connected in series each wafer
    output action synchronization.
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            sdo = F.ElectricLogic()
            sdi = F.ElectricLogic()
            cko = F.ElectricLogic()
            ckl = F.ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.sdo.IFs.signal,
                    "2": x.power.IFs.lv,
                    "3": x.sdi.IFs.signal,
                    "4": x.ckl.IFs.signal,
                    "5": x.power.IFs.hv,
                    "6": x.cko.IFs.signal,
                }
            )
        )

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        self.add_trait(
            F.has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/2110250930_OPSCO-Optoelectronics-SK9822-EC20_C2909059.pdf"
            )
        )

        self.add_trait(F.has_designator_prefix_defined("F.LED"))
