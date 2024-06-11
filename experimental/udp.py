import socket

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to a specific address and port
udp_socket.bind(('0.0.0.0', 8500))

# Listen for incoming UDP packets
while True:
  data, addr = udp_socket.recvfrom(65535)  # Use the maximum UDP packet size
  print(f'Received data from {addr}: {data}')

# Close the socket
udp_socket.close()