from faebryk.core.module import Module 
from faebryk.libs.library import L
import faebryk.library._F as F
from faebryk.libs.units import P

from vindriktning.blocks.FanController import FanController

class App(Module):
    r: F.Resistor
    fan_connector: FanController

    def __preinit__(self):
        self.r.resistance.constrain_subset(L.Range.from_center_rel(5.1 * P.kohm, 5 * P.percent))
        self.r.add(F.has_package(F.has_package.Package.R0402))
        


