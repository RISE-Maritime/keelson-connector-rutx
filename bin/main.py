import zenoh
import logging
import warnings
import atexit
import json
import time
import keelson
from terminal_inputs import terminal_inputs
import socket   
from keelson.payloads.TimestampedBytes_pb2 import TimestampedBytes
from keelson.payloads.TimestampedString_pb2 import TimestampedString
from keelson.payloads.Log_pb2 import Log
from keelson.payloads.NMEA_pb2 import GNGNS
import pynmea2


session = None
args = None


if __name__ == "__main__":
    # Input arguments and configurations
    args = terminal_inputs()
    # Setup logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s", level=args.log_level
    )
    logging.captureWarnings(True)
    warnings.filterwarnings("once")

    ## Construct session
    logging.info("Opening Zenoh session...")
    conf = zenoh.Config()
    if args.connect is not None:
        conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
    session = zenoh.open(conf)

    def _on_exit():
        session.close()

    atexit.register(_on_exit)
    logging.info(f"Zenoh session established: {session.info()}")

    #################################################
    # Setting up PUBLISHER

    # RAW NMEA publisher
    key_exp_pub_raw = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="raw",  # Needs to be a supported subject
        source_id=args.source_id,
    )
    pub_raw = session.declare_publisher(
        key_exp_pub_raw,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_raw}")

    # RAW STRING NMEA publisher
    key_exp_pub_raw_str = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="raw_string",  # Needs to be a supported subject
        source_id=args.source_id,
    )
    pub_raw_str= session.declare_publisher(
        key_exp_pub_raw_str,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_raw_str}")

    # LOG NMEA publisher
    key_exp_pub_log = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="log",  # Needs to be a supported subject
        source_id=args.source_id,
    )
    pub_log = session.declare_publisher(
        key_exp_pub_log,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_log}")

    # NMEA GNGNS publisher 
    key_exp_pub_nmea_gngns = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="nmea_gngns",  # Needs to be a supported subject
        source_id=args.source_id,
    )
    pub_nmea_gngns = session.declare_publisher(
        key_exp_pub_nmea_gngns,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_nmea_gngns}")


    try:

        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind the socket to a specific address and port
        udp_socket.bind(('0.0.0.0', args.udp_port))

        # Listen for incoming UDP packets
        while True:
            data, addr = udp_socket.recvfrom(65535)  # Use the maximum UDP packet size
            ingress_timestamp = time.time_ns()

            logging.debug(f'Received data from {addr}: {data}')

            if "raw" in args.publish:
                logging.debug("Publish RAW message...")
                payload = TimestampedBytes()
                payload.timestamp.FromNanoseconds(ingress_timestamp)
                payload.value = data
                serialized_payload = payload.SerializeToString()
                envelope = keelson.enclose(serialized_payload)
                pub_raw.put(envelope)
                logging.debug(f"...published on {key_exp_pub_raw}")

            if "raw_string" in args.publish:
                logging.debug("Publish RAW STRING message...")
                payload = TimestampedString()
                payload.timestamp.FromNanoseconds(ingress_timestamp)
                payload.value = data
                serialized_payload = payload.SerializeToString()
                envelope = keelson.enclose(serialized_payload)
                pub_raw_str.put(envelope)
                logging.debug(f"...published on {key_exp_pub_raw_str}")
            
            if "log" in args.publish:
                logging.debug("Publish LOG message...")
                payload = Log()
                payload.timestamp.FromNanoseconds(ingress_timestamp)
                payload.level = Log.Level.INFO
                payload.message = f"Received data from UDP socket. {data}"
                payload.name = "INFO_UDP_SOCKET"
                payload.file = "main.py"
                payload.line = 107
                serialized_payload = payload.SerializeToString()
                envelope = keelson.enclose(serialized_payload)
                pub_log.put(envelope)
                logging.debug(f"...published on {key_exp_pub_log}")
            
            if "nmea" in args.publish:
                logging.debug("Parsing NMEA message...")
                # Parsing NMEA data
                try:
                    nmea_sentence = data.decode("utf-8")
                    if nmea_sentence.split(',')[0] != "$GNGNS":
                        nmea_data = pynmea2.parse(nmea_sentence)
                        payload = GNGNS()
                        payload.timestamp.FromNanoseconds(ingress_timestamp)
                        payload.utc.FromDatetime(nmea_data.timestamp)
                        # Latitude 
                        if nmea_sentence.lat_dir == "S":
                            payload.latitude = float(-nmea_data.lat)
                        else:
                            payload.latitude = float(nmea_data.lat)
                        # Longitude 
                        if nmea_sentence.lon_dir == "W":
                            payload.longitude = float(-nmea_data.lon)
                        else:
                            payload.longitude = float(nmea_data.longitude)

                        payload.mode_indicator = str(nmea_data.mode_indicator)
                        payload.satellites_used = int(nmea_data.num_sats)
                        payload.hdop = float(nmea_data.hdop)
                        payload.altitude = float(nmea_data.altitude)
                        payload.geoid_height = float(nmea_data.geo_sep)
                        serialized_payload = payload.SerializeToString()
                        envelope = keelson.enclose(serialized_payload)
                        pub_log.put(envelope)
                        logging.debug(f"...published on {key_exp_pub_nmea_gngns}")



                except Exception as e:
                    logging.error(f"Error parsing NMEA data: {e}")
                    payload.value = data.decode("utf-8")
                nmea_data = data.decode("utf-8")


                payload.utc = "2"

   
        # Close the socket
        udp_socket.close()


    except KeyboardInterrupt:
        logging.info("Closing down on user request!")
        # Close the socket
        udp_socket.close()
        logging.debug("Done! Good bye :)")