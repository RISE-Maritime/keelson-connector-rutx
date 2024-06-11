import socket

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to a specific address and port
udp_socket.bind(('localhost', 5800))

# Listen for incoming UDP packets
while True:
  data, addr = udp_socket.recvfrom(1024)
  print(f'Received data from {addr}: {data.decode()}')

# Close the socket
udp_socket.close()


