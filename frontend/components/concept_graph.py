
from pyvis.network import Network
import tempfile


def render_graph(graph):

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#111827",
        font_color="white",
        directed=False
    )

    # Normalize node names and create a lookup set
    nodes = {
        str(node).strip()
        for node in graph.get("nodes", [])
        if node is not None
    }

    # Add all valid nodes
    for node in nodes:
        net.add_node(
            node,
            label=node,
            size=25
        )

    # Add only edges whose endpoints exist
    for edge in graph.get("edges", []):

        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            continue

        source = str(edge[0]).strip()
        target = str(edge[1]).strip()

        if source in nodes and target in nodes:
            net.add_edge(source, target)

    net.repulsion(
        node_distance=220,
        central_gravity=0.25,
        spring_length=160,
        spring_strength=0.05
    )

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".html"
    )

    temp.close()

    net.save_graph(temp.name)

    return temp.name
