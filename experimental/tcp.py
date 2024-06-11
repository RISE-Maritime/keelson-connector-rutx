import socket

def tcp_connector():
  # Create a TCP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # Define the server address and port
  server_address = ('localhost', 8501)

  try:
    # Connect to the server
    sock.connect(server_address)
    print('Connected to {}:{}'.format(*server_address))

    # Perform any necessary operations with the connected socket here

  except ConnectionRefusedError:
    print('Connection refused. Make sure the server is running.')

  finally:
    # Close the socket
    sock.close()

# Call the tcp_connector function to establish the connection
tcp_connector()