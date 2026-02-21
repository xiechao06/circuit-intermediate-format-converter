import uuid
from functools import cached_property
from typing import Any

from loguru import logger

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.label import Label
from cifconv.net import Net
from cifconv.no_connect import NoConnect
from cifconv.pin_instance import PinInstance
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
        self.no_connects: list[NoConnect] = []
        self.bus_entries: dict[str, BusEntry] = {}

    def to_json(self) -> dict[str, Any]:
        net_name_to_id: dict[str, str] = {}
        for net in self.nets:
            net_name_to_id[net.name] = net.uuid

        buses_json: list[dict[str, Any]] = []
        for bus in self.buses.values():
            net_name = None
            for net in self.nets:
                if bus in net.buses:
                    net_name = net.name
                    break
            buses_json.append(
                {
                    "name": bus.uuid,
                    "net": net_name_to_id.get(net_name, "") if net_name else "",
                    "points": [{"x": p.x, "y": p.y} for p in bus.points],
                    "uuid": bus.uuid,
                }
            )

        instances_json: list[dict[str, Any]] = []
        for instance in self.instances:
            instances_json.append(
                {
                    "attributes": instance.attributes or {},
                    "designator": instance.designator,
                    "lib_id": instance.lib_id,
                    "placement": {
                        "mirror": False,
                        "rotation": instance.rotation,
                        "x": instance.x,
                        "y": instance.y,
                    },
                    "uuid": instance.uuid,
                }
            )

        library_json: list[dict[str, Any]] = []
        for lib_id, symbol in self.symbols.items():
            pins_json: list[dict[str, Any]] = []
            for pin in symbol.pins:
                pins_json.append(
                    {
                        "id": pin.number,
                        "name": pin.name,
                        "rel_x": pin.rel_x,
                        "rel_y": pin.rel_y,
                        "type": pin.type or "unspecified",
                    }
                )
            library_json.append(
                {
                    lib_id: {
                        "pins": pins_json,
                        "ref": symbol.ref,
                        "type": symbol.type or "",
                    }
                }
            )

        nets_json: list[dict[str, Any]] = []
        for net in self.nets:
            pins_json: list[dict[str, Any]] = []
            if net.connected_pins:
                for instance, pin in net.connected_pins:
                    pins_json.append(
                        {
                            "pin": pin.number,
                            "ref": instance.designator,
                        }
                    )
            nets_json.append(
                {
                    "name": net.name,
                    "net_id": net.uuid,
                    "pins": pins_json,
                }
            )

        wires_json: list[dict[str, Any]] = []
        for wire in self.wires.values():
            net_name = None
            for net in self.nets:
                if wire in net.wires:
                    net_name = net.name
                    break
            wires_json.append(
                {
                    "net": net_name_to_id.get(net_name, "") if net_name else "",
                    "points": [{"x": p.x, "y": p.y} for p in wire.points],
                    "uuid": wire.uuid,
                }
            )

        return {
            "buses": buses_json,
            "instances": instances_json,
            "library": library_json,
            "nets": nets_json,
            "wires": wires_json,
        }

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
            """
            Find the root representative of the connected component that contains the given element.

            This helper implements the 'find' operation of a Union-Find (Disjoint-Set Union) data
            structure. It returns the canonical tuple that represents the entire connected group
            to which the supplied element belongs. Path compression is applied so that future
            queries for the same element (and its ancestors) are faster.

            Parameters
            ----------
            element : tuple[str, str]
                A 2-tuple consisting of (element_type, element_uuid) that uniquely identifies
                a schematic element (wire, bus, or bus entry).

            Returns
            -------
            tuple[str, str]
                The root tuple of the connected component. All elements sharing the same root
                are electrically connected.
            """
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

        no_connect_positions: set[Point] = set()
        for no_connect in self.no_connects:
            no_connect_positions.add(Point(no_connect.x, no_connect.y))

        pin_pos_to_instance: dict[Point, tuple[SymbolInstance, PinInstance]] = {}
        for instance in self.instances:
            if instance.pin_instances:
                for pin in instance.pin_instances:
                    pin_pos = Point(pin.x, pin.y)
                    if pin_pos in no_connect_positions:
                        logger.debug(f"Pin {pin} at {pin_pos} is no connect position")
                        continue
                    pin_pos_to_instance[pin_pos] = (instance, pin)

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

            points_for_net: list[Point] = []
            for point, grp in net_point_to_group.items():
                if grp == group_root:
                    points_for_net.append(point)

            connected_pins_for_net: list[tuple[SymbolInstance, PinInstance]] = []
            for point, grp in net_point_to_group.items():
                if grp == group_root and point in pin_pos_to_instance:
                    connected_pins_for_net.append(pin_pos_to_instance[point])

            net_obj = Net(
                uuid=str(uuid.uuid4()),
                name=net_name,
                wires=wires_for_net,
                buses=buses_for_net,
                bus_entries=bus_entries_for_net,
                points=points_for_net,
                connected_pins=connected_pins_for_net
                if connected_pins_for_net
                else None,
            )
            net_objects.append(net_obj)

        return net_objects
