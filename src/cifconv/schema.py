from functools import cached_property

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.junction import Junction
from cifconv.label import Label
from cifconv.net import Net
from cifconv.no_connect import NoConnect
from cifconv.point import Point
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance
from cifconv.wire import Wire


class Schema:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}
        self.instances: list[SymbolInstance] = []
        self.wires: dict[str, Wire] = {}
        self.buses: dict[str, Bus] = {}
        self.labels: list[Label] = []
        self.junctions: dict[str, Junction] = {}
        self.no_connects: list[NoConnect] = []
        self.bus_entries: dict[str, BusEntry] = {}

    @cached_property
    def nets(self) -> list["Net"]:
        """
        Returns a list of Net objects based on connected components in the schematic.

        A net is formed by electrically connected elements (wires, buses, bus entries).
        Junctions are not used for connectivity detection because in KiCad, when a junction
        is placed on a wire, the wire is split into segments with the junction position as
        an endpoint. Therefore, connectivity can be determined purely from wire/bus points.
        If a net contains a label, it is named after that label.
        Otherwise, it is named as 'net_{n}' where n is the sequence number.
        """
        from cifconv.bus import Bus
        from cifconv.bus_entry import BusEntry
        from cifconv.junction import Junction
        from cifconv.wire import Wire

        coord_to_elements: dict[Point, list[tuple[str, str]]] = {}

        for wire in self.wires.values():
            for point in wire.points:
                if point not in coord_to_elements:
                    coord_to_elements[point] = []
                coord_to_elements[point].append(("wire", wire.uuid))

        for bus in self.buses.values():
            for point in bus.points:
                if point not in coord_to_elements:
                    coord_to_elements[point] = []
                coord_to_elements[point].append(("bus", bus.uuid))

        for bus_entry in self.bus_entries.values():
            start_point = bus_entry.start_point
            end_point = bus_entry.end_point

            if start_point not in coord_to_elements:
                coord_to_elements[start_point] = []
            coord_to_elements[start_point].append(("bus_entry", bus_entry.uuid))

            if end_point not in coord_to_elements:
                coord_to_elements[end_point] = []
            coord_to_elements[end_point].append(("bus_entry", bus_entry.uuid))

        element_to_group: dict[tuple[str, str], tuple[str, str]] = {}

        def find(element: tuple[str, str]) -> tuple[str, str]:
            if element not in element_to_group:
                element_to_group[element] = element
                return element
            if element_to_group[element] != element:
                element_to_group[element] = find(element_to_group[element])
            return element_to_group[element]

        def union(elem1: tuple[str, str], elem2: tuple[str, str]) -> None:
            root1 = find(elem1)
            root2 = find(elem2)
            if root1 != root2:
                element_to_group[root1] = root2

        for elements in coord_to_elements.values():
            for element in elements:
                find(element)

        for elements in coord_to_elements.values():
            if len(elements) > 1:
                first_element = elements[0]
                for other_element in elements[1:]:
                    union(first_element, other_element)

        groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for element in element_to_group.keys():
            root = find(element)
            if root not in groups:
                groups[root] = []
            groups[root].append(element)

        coord_to_label: dict[Point, str] = {}
        for label in self.labels:
            coord_to_label[Point(label.x, label.y)] = label.text

        group_labels: dict[tuple[str, str], str] = {}
        for group_root, elements in groups.items():
            labels_for_group: set[str] = set()
            for elem_type, elem_uuid in elements:
                if elem_type == "wire":
                    wire = self.wires[elem_uuid]
                    for point in wire.points:
                        if point in coord_to_label:
                            labels_for_group.add(coord_to_label[point])
                elif elem_type == "bus":
                    bus = self.buses[elem_uuid]
                    for point in bus.points:
                        if point in coord_to_label:
                            labels_for_group.add(coord_to_label[point])
                elif elem_type == "bus_entry":
                    bus_entry = self.bus_entries[elem_uuid]
                    start_point = bus_entry.start_point
                    end_point = bus_entry.end_point
                    if start_point in coord_to_label:
                        labels_for_group.add(coord_to_label[start_point])
                    if end_point in coord_to_label:
                        labels_for_group.add(coord_to_label[end_point])

            if labels_for_group:
                group_labels[group_root] = next(iter(labels_for_group))

        net_point_to_group: dict[Point, tuple[str, str]] = {}
        for group_root, elements in groups.items():
            for elem_type, elem_uuid in elements:
                if elem_type == "wire":
                    wire = self.wires[elem_uuid]
                    for point in wire.points:
                        net_point_to_group[point] = group_root
                elif elem_type == "bus":
                    bus = self.buses[elem_uuid]
                    for point in bus.points:
                        net_point_to_group[point] = group_root
                elif elem_type == "bus_entry":
                    bus_entry = self.bus_entries[elem_uuid]
                    net_point_to_group[bus_entry.start_point] = group_root
                    net_point_to_group[bus_entry.end_point] = group_root

        junction_to_group: dict[str, tuple[str, str]] = {}
        for junction in self.junctions.values():
            point = Point(junction.x, junction.y)
            if point in net_point_to_group:
                junction_to_group[junction.uuid] = net_point_to_group[point]

        net_objects: list[Net] = []
        net_counter: int = 0

        for group_root in sorted(groups.keys()):
            if group_root in group_labels:
                net_name = group_labels[group_root]
            else:
                net_name = f"net_{net_counter}"
                net_counter += 1

            wires_for_net: list[Wire] = []
            buses_for_net: list[Bus] = []
            bus_entries_for_net: list[BusEntry] = []

            for elem_type, elem_uuid in groups[group_root]:
                if elem_type == "wire":
                    wires_for_net.append(self.wires[elem_uuid])
                elif elem_type == "bus":
                    buses_for_net.append(self.buses[elem_uuid])
                elif elem_type == "bus_entry":
                    bus_entries_for_net.append(self.bus_entries[elem_uuid])

            junctions_for_net: list[Junction] = []
            for junction_uuid, grp in junction_to_group.items():
                if grp == group_root:
                    junctions_for_net.append(self.junctions[junction_uuid])

            net_obj = Net(
                name=net_name,
                wires=wires_for_net,
                buses=buses_for_net,
                junctions=junctions_for_net,
                bus_entries=bus_entries_for_net,
            )
            net_objects.append(net_obj)

        return net_objects
