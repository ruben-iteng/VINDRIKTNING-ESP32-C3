import faebryk.library._F as F
from faebryk.core.module import Module


class MCU(Module):
    # TODO: Currently no other way to make a build target out of this
    mcu: F.ESP32_C3_MINI_1_ReferenceDesign
