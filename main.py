import argparse
import xml.etree.ElementTree as ET

PUT_INTO_LORRY = 1000 # time to put a source into lorry = 1s
def parse_log_file(log_file_path):
    # Parse the log file and extract worker actions and resources
    worker_actions = []
    lorry_actions = []

    with open(log_file_path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.split()

            #Working with workers and its statistics
            if "vytěžil zdroj" in line:
                action_id = parts[4]
                time_to_mine = int(parts[10])
                if action_id not in [action['id'] for action in worker_actions]:
                    worker_actions.append({"id": action_id, "resource_count": 1, "time_to_mine": time_to_mine})
                else:
                    # Pokud id dělníka již existuje, zvýš počet zdrojů o 1
                    worker_index = [action['id'] for action in worker_actions].index(action_id)
                    worker_actions[worker_index]["resource_count"] += 1
                    worker_actions[worker_index]["time_to_mine"] += time_to_mine
            if "nakládá" in line:
                action_id = parts[4]
                worker_index = [action['id'] for action in worker_actions].index(action_id)
                worker_actions[worker_index]["time_to_mine"] += PUT_INTO_LORRY

            #Working with lorries and its statistics
            if "připraven vyrazit" in line:
                action_id = parts[4]
                if action_id not in [action['id'] for action in lorry_actions]:
                    lorry_actions.append({"id": action_id, "time_to_fill": parts[12], "transport_time": 0})


    return worker_actions, lorry_actions

def generate_xml(worker_actions, lorry_actions, output_file_path):
    # Sort worker actions by ID
    sorted_worker_actions = sorted(worker_actions, key=lambda x: x["id"])
    sorted_lorry_actions = sorted(lorry_actions, key=lambda x: x["id"])
    # Create XML structure
    root = ET.Element("Simulation")
    root.set("duration", "YZ")

    # Create Workers element
    workers_element = ET.SubElement(root, "Workers")
    vehicles_element = ET.SubElement(root, "Vehicles")  # Create Vehicles element

    # Create XML elements for sorted worker actions
    for worker_action in sorted_worker_actions:
        worker_element = ET.SubElement(workers_element, "Worker")
        worker_element.set("id", worker_action["id"])

        resource_element = ET.SubElement(worker_element, "resources")
        resource_element.text = str(worker_action["resource_count"])

        workerDuration_element = ET.SubElement(worker_element, "workDuration")
        workerDuration_element.text = str(worker_action["time_to_mine"]) + " ms"

    # Create XML elements for sorted lorry actions
    for lorry_action in sorted_lorry_actions:
        lorry_element = ET.SubElement(vehicles_element, "Vehicle")  # Create Vehicle element under Vehicles
        lorry_element.set("id", lorry_action["id"])

        loadTime_element = ET.SubElement(lorry_element, "loadTime")
        loadTime_element.text = str(lorry_action["time_to_fill"]) + " ms"

    # Create an ElementTree object
    tree = ET.ElementTree(root)

    # Write the XML tree to a file
    tree.write(output_file_path, encoding="utf-8", xml_declaration=False)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Parse log file and generate XML output")
    parser.add_argument("-i", "--input", help="Input log file path", required=True)
    parser.add_argument("-o", "--output", help="Output XML file path", required=True)
    args = parser.parse_args()

    # Parse log file
    worker_actions, lorry_actions = parse_log_file(args.input)

    # Generate XML
    generate_xml(worker_actions, lorry_actions,  args.output)

if __name__ == "__main__":
    main()