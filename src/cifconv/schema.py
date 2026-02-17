from functools import cached_property

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.junction import Junction
from cifconv.label import Label
from cifconv.net import Net
from cifconv.noconnect import NoConnect
from cifconv.point import Point
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance
from cifconv.wire import Wire


class Schema:
    def __init__(self):
        self.symbols: list[Symbol] = []
        self.instances: list[SymbolInstance] = []
        self.wires: list[Wire] = []
        self.buses: list[Bus] = []
        self.labels: list[Label] = []
        self.junctions: list[Junction] = []
        self.noconnects: list[NoConnect] = []
        self.bus_entries: list[BusEntry] = []

    @cached_property
    def nets(self) -> list["Net"]:
        """
        Returns a list of Net objects based on connected components in the schematic.

        A net is formed by electrically connected elements (wires, buses, junctions, bus entries).
        If a net contains a label, it is named after that label.
        Otherwise, it is named as 'net_{n}' where n is the sequence number.
        """
        from cifconv.bus import Bus
        from cifconv.bus_entry import BusEntry
        from cifconv.junction import Junction
        from cifconv.wire import Wire

        # Create a mapping from coordinates to elements that contain those coordinates
        coord_to_elements: dict[Point, list[tuple[str, str]]] = {}

        # Add wires to coordinate map
        for wire in self.wires:
            for point in wire.points:
                if point not in coord_to_elements:
                    coord_to_elements[point] = []
                coord_to_elements[point].append(("wire", wire.uuid))

        # Add buses to coordinate map
        for bus in self.buses:
            for point in bus.points:
                if point not in coord_to_elements:
                    coord_to_elements[point] = []
                coord_to_elements[point].append(("bus", bus.uuid))

        # Add junctions to coordinate map
        for junction in self.junctions:
            point = Point(junction.x, junction.y)
            if point not in coord_to_elements:
                coord_to_elements[point] = []
            coord_to_elements[point].append(("junction", junction.uuid))

        # Add bus entries to coordinate map (both start and end points)
        for bus_entry in self.bus_entries:
            start_point = bus_entry.start_point
            end_point = bus_entry.end_point

            if start_point not in coord_to_elements:
                coord_to_elements[start_point] = []
            coord_to_elements[start_point].append(("bus_entry", bus_entry.uuid))

            if end_point not in coord_to_elements:
                coord_to_elements[end_point] = []
            coord_to_elements[end_point].append(("bus_entry", bus_entry.uuid))

        # Find connected components using Union-Find algorithm
        element_to_group: dict[tuple[str, str], tuple[str, str]] = {}

        def find(element: tuple[str, str]) -> tuple[str, str]:
            """
            Find the root element of a group using path compression.

            This function implements the "find" operation of a Union-Find (Disjoint Set Union)
            data structure. It locates the root representative of the group that contains
            the given element and optimizes future lookups by compressing the path.

            Args:
                element (tuple[str, str]): A tuple representing an element to find its group root.

            Returns:
                tuple[str, str]: The root element of the group containing the input element.

            Note:
                This function modifies the `element_to_group` dictionary to implement path
                compression, which flattens the tree structure and improves performance of
                subsequent find operations.
            """
            if element not in element_to_group:
                element_to_group[element] = element
                return element
            # Path compression
            if element_to_group[element] != element:
                element_to_group[element] = find(element_to_group[element])
            return element_to_group[element]

        def union(elem1: tuple[str, str], elem2: tuple[str, str]) -> None:
            root1 = find(elem1)
            root2 = find(elem2)
            if root1 != root2:
                element_to_group[root1] = root2

        # Initialize all elements in the union-find structure
        for elements in coord_to_elements.values():
            for element in elements:
                find(element)  # Ensure element is initialized in the structure

        # Connect elements that share coordinates
        for elements in coord_to_elements.values():
            if len(elements) > 1:
                # Connect all elements at this coordinate
                first_element = elements[0]
                for other_element in elements[1:]:
                    union(first_element, other_element)

        # Group elements by their connected component
        groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for element in element_to_group.keys():
            root = find(element)
            if root not in groups:
                groups[root] = []
            groups[root].append(element)

        # Associate labels with connected components
        # Create a coordinate to label mapping
        coord_to_label: dict[Point, str] = {}
        for label in self.labels:
            coord_to_label[Point(label.x, label.y)] = label.text

        # Map each group to its labels
        group_labels: dict[tuple[str, str], str] = {}
        for group_root, elements in groups.items():
            labels_for_group: set[str] = set()
            for elem_type, elem_uuid in elements:
                # Check if this element's coordinates match any label
                if elem_type == "wire":
                    wire = next(w for w in self.wires if w.uuid == elem_uuid)
                    for point in wire.points:
                        if point in coord_to_label:
                            labels_for_group.add(coord_to_label[point])
                elif elem_type == "bus":
                    bus = next(b for b in self.buses if b.uuid == elem_uuid)
                    for point in bus.points:
                        if point in coord_to_label:
                            labels_for_group.add(coord_to_label[point])
                elif elem_type == "junction":
                    junction = next(j for j in self.junctions if j.uuid == elem_uuid)
                    point = Point(junction.x, junction.y)
                    if point in coord_to_label:
                        labels_for_group.add(coord_to_label[point])
                elif elem_type == "bus_entry":
                    bus_entry = next(
                        be for be in self.bus_entries if be.uuid == elem_uuid
                    )
                    start_point = bus_entry.start_point
                    end_point = bus_entry.end_point
                    if start_point in coord_to_label:
                        labels_for_group.add(coord_to_label[start_point])
                    if end_point in coord_to_label:
                        labels_for_group.add(coord_to_label[end_point])

            # Assign the first label found to this group, or None if no label
            if labels_for_group:
                group_labels[group_root] = next(
                    iter(labels_for_group)
                )  # Take first label

        # Generate Net objects
        net_objects: list[Net] = []
        net_counter: int = 0

        for group_root in sorted(groups.keys()):  # Sort to ensure consistent ordering
            # Determine net name
            if group_root in group_labels:
                net_name = group_labels[group_root]
            else:
                net_name = f"net_{net_counter}"
                net_counter += 1

            # Collect elements for this net
            wires_for_net: list[Wire] = []
            buses_for_net: list[Bus] = []
            junctions_for_net: list[Junction] = []
            bus_entries_for_net: list[BusEntry] = []

            for elem_type, elem_uuid in groups[group_root]:
                if elem_type == "wire":
                    wire = next(w for w in self.wires if w.uuid == elem_uuid)
                    wires_for_net.append(wire)
                elif elem_type == "bus":
                    bus = next(b for b in self.buses if b.uuid == elem_uuid)
                    buses_for_net.append(bus)
                elif elem_type == "junction":
                    junction = next(j for j in self.junctions if j.uuid == elem_uuid)
                    junctions_for_net.append(junction)
                elif elem_type == "bus_entry":
                    bus_entry = next(
                        be for be in self.bus_entries if be.uuid == elem_uuid
                    )
                    bus_entries_for_net.append(bus_entry)

            # Create Net object
            net_obj = Net(
                name=net_name,
                wires=wires_for_net,
                buses=buses_for_net,
                junctions=junctions_for_net,
                bus_entries=bus_entries_for_net,
            )
            net_objects.append(net_obj)

        return net_objects
