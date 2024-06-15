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
        subject="raw_str",  # Needs to be a supported subject
        source_id=args.source_id,
    )
    pub_raw_str= session.declare_publisher(
        key_exp_pub_raw_str,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_raw_str}")

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
                payload = TimestampedBytes()
                payload.timestamp.FromNanoseconds(ingress_timestamp)
                payload.value = data
                serialized_payload = payload.SerializeToString()
                envelope = keelson.enclose(serialized_payload)
                pub_raw_str.put(envelope)
                logging.debug(f"...published on {key_exp_pub_raw_str}")


   
        # Close the socket
        udp_socket.close()


    except KeyboardInterrupt:
        logging.info("Closing down on user request!")
        # Close the socket
        udp_socket.close()
        logging.debug("Done! Good bye :)")