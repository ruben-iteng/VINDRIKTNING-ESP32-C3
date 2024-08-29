import faebryk.library._F as F
from faebryk.core.node import Node


def get_decoupling_caps(node: Node) -> set[F.Capacitor]:
    return {
        c.get_trait(F.is_decoupled).get_capacitor()
        for c in node.get_children(
            direct_only=False,
            f_filter=lambda x: x.has_trait(F.is_decoupled),
            types=Node,
        )
    }
