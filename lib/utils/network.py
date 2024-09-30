import http.client
import time


def get_upload_time(
    server: str = "httpbin.org",
    path: str = "/post",
    port: int = 443,
    file_size_mb: int = 500,
) -> float:
    """
    Estimates the time (in seconds) to upload a file of the given size (in MB)
    to a server by calculating upload speed using a 1 MB sample upload.
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

    return file_size_mb / upload_speed_mbps


def measure_upload_speed(
    server: str = "httpbin.org",
    path: str = "/post",
    port: int = 443,
) -> float:
    """
    Measures upload speed to a given server by sending a 1 MB sample data and
    calculating the speed in megabits per second (Mbps).
    :param server: The domain name of the server to which data is uploaded.
    :param path: The path on the server where the POST request will be sent.
    :param port: The port for the HTTPS connection, default is 443.
    :return: The upload speed in Mbps.
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

    return upload_speed_mbps
