import http.client
import time


def calculate_upload_time(
    server: str = "httpbin.org",
    path: str = "/post",
    port: int = 443,
    file_size_mb: int = 500,
) -> float:
    """
    Measures the upload speed by sending a file of specified size to a server.
    :param server: The server to send the POST request to. Defaults to 'httpbin.org'.
    :param path: The path on the server to send the POST request to. Defaults to '/post'.
    :param port: The port to connect to. Defaults to 443 for HTTPS.
    :param file_size_mb: The size of the file to simulate the upload, in MB. Defaults to 500MB.
    :return: The calculated upload speed in Mbps.
    """
    conn = http.client.HTTPSConnection(server, port)
    sample_data = b"x" * (1024 * 1024)
    headers = {
        "Content-type": "application/octet-stream",
    }

    start_time = time.time()
    conn.request("POST", path, body=sample_data, headers=headers)
    response = conn.getresponse()
    response.read()
    end_time = time.time()

    elapsed_time = end_time - start_time
    upload_speed_mbps = (8 * len(sample_data)) / (elapsed_time * 1024 * 1024)
    conn.close()

    return (file_size_mb * 8) / upload_speed_mbps
