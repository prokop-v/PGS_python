import argparse
import xml.etree.ElementTree as ET
from datetime import datetime

"""
Constants
"""
PUT_INTO_LORRY = 10  # time to put a source into lorry = 1s
WORKER_MINED_A_SOURCE = "vytěžil zdroj"
W_INTO_LORRY = "nakládá"
LORRY_READY_TO_GO = "připraven vyrazit"
WORKER_MINED_A_BLOCK = "vytěžil celý blok"
FERRY_DEPARTURE = "Trajekt"
LORRY_AT_FERRY = "dojel k trajektu"
LORRY_AT_THE_END = "přijel na místo"

"""
Global Variables
"""
blocks_mined = [0, 0]
sources_mined = [0, 0]



def parse_log_file(log_file_path):
    # Parse the log file and extract worker actions and resources
    worker_actions = []
    lorry_actions = []
    ferry_actions = [0, 0]

    with open(log_file_path, "r", encoding="utf-8") as file:
        first_line = True
        start_time_simulation = ""

        for line in file:
            parts = line.split()

            if(first_line):
                start_time_simulation = parts[0] +" "+ parts[1]
                first_line = False

            # Working with workers and its statistics
            if WORKER_MINED_A_SOURCE in line:
                sources_mined[0] += 1
                action_id = parts[4]

                if action_id not in [action['id'] for action in worker_actions]:
                    worker_actions.append({"id": action_id, "resource_count": 1, "work_time": 0.0})
                else:
                    # Pokud id dělníka již existuje, zvýš počet zdrojů o 1
                    worker_index = [action['id'] for action in worker_actions].index(action_id)
                    worker_actions[worker_index]["resource_count"] += 1

            if WORKER_MINED_A_BLOCK in line:
                blocks_mined[0] += 1
                blocks_mined[1] += int(parts[11])

            if W_INTO_LORRY in line:
                action_id = parts[4]
                worker_index = [action['id'] for action in worker_actions].index(action_id)
                worker_actions[worker_index]["work_time"] = time(start_time_simulation, parts[0] + " " + parts[1])

            # Working with lorries and its statistics
            if LORRY_READY_TO_GO in line:
                action_id = parts[4]
                if action_id not in [action['id'] for action in lorry_actions]:
                    lorry_actions.append({"id": action_id, "time_to_fill": parts[12], "transport_time": 0})

            if LORRY_AT_FERRY in line:
                action_id = parts[4]
                lorry_index = [action['id'] for action in lorry_actions].index(action_id)
                lorry_actions[lorry_index]["transport_time"] += int(parts[11])

            if LORRY_AT_THE_END in line:
                action_id = parts[4]
                lorry_index = [action['id'] for action in lorry_actions].index(action_id)
                lorry_actions[lorry_index]["transport_time"] += int(parts[12])
                end_time = parts[0] + " " + parts[1]

            #working with ferry
            if FERRY_DEPARTURE in line:
                ferry_actions[0] += 1
                ferry_actions[1] += int(parts[8])


    simulation_t = time(start_time_simulation, end_time)
    return worker_actions, lorry_actions, ferry_actions, simulation_t

def time(start_time, end_time):
    format_str = "%d.%m.%Y %H:%M:%S.%f"

    t1 = datetime.strptime(start_time, format_str)
    t2 = datetime.strptime(end_time, format_str)

    return (t2 - t1).total_seconds() * 1000

def generate_xml(worker_actions, lorry_actions, ferry_actions, simulation_t, output_file_path):
    # Sort worker actions by ID
    sorted_worker_actions = sorted(worker_actions, key=lambda x: int(x["id"]))
    sorted_lorry_actions = sorted(lorry_actions, key=lambda x: int(x["id"]))

    # Create XML structure
    root = ET.Element("Simulation")
    root.set("duration", str(simulation_t) + " ms")

    #Mined blocks
    blocks_average_duration_element = ET.SubElement(root, "blockAverageDuration")
    blocks_average_duration_element.set("totalCount", str(blocks_mined[0]))
    blocks_average_duration_element.text = str(round((blocks_mined[1] / blocks_mined[0]), 3)) + " ms"

    #Mined sources
    source_average_duration_element = ET.SubElement(root, "resourceAverageDuration")
    source_average_duration_element.set("totalCount", str(sources_mined[0]))
    source_average_duration_element.text = str(round((sources_mined[1]/sources_mined[0]), 3)) + " ms"

    #Ferry logs
    ferry_average_time_element = ET.SubElement(root, "ferryAverageWait")
    ferry_average_time_element.set("trips", str(ferry_actions[0]))
    average_wait_time = round(ferry_actions[1] / ferry_actions[0], 3)
    ferry_average_time_element.text = str(average_wait_time) + " ms"

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
        workerDuration_element.text = str(worker_action["work_time"]) + " ms"

    # Create XML elements for sorted lorry actions
    for lorry_action in sorted_lorry_actions:
        lorry_element = ET.SubElement(vehicles_element, "Vehicle")  # Create Vehicle element under Vehicles
        lorry_element.set("id", lorry_action["id"])

        loadTime_element = ET.SubElement(lorry_element, "loadTime")
        loadTime_element.text = str(lorry_action["time_to_fill"]) + " ms"
        transportTime_element = ET.SubElement(lorry_element, "transportTime")
        transportTime_element.text = str((lorry_action["transport_time"] + average_wait_time)) + " ms"

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
    worker_actions, lorry_actions, ferry_actions, simulation_t = parse_log_file(args.input)

    # Generate XML
    generate_xml(worker_actions, lorry_actions, ferry_actions, simulation_t, args.output)

if __name__ == "__main__":
    main()
