import http.client
import time

from lib.schemas.network import ApiResponse, HTTPRequestMethod
from requests import JSONDecodeError, Response


def estimate_upload_time(
    server: str = "httpbin.org",
    path: str = "/post",
    port: int = 443,
    file_size_mb: int | None = None,
) -> float:
    """
    Estimates the upload speed or time required to upload a file of a specified size to a server.
    :param server: The server hostname or IP address to upload the file to. Default is 'httpbin.org'.
    :param path: The path to the server resource where the file will be uploaded. Default is '/post'.
    :param port: The port to use for the HTTPS connection. Default is 443.
    :param file_size_mb: The size of the file in megabytes to estimate upload time. If None, returns the upload speed in MBps.
    :return: The estimated upload time in seconds for the given file size, or the upload speed in MBps if file_size_mb is None.
    :raises ConnectionError: If the server connection or request fails.
    """
    conn = http.client.HTTPSConnection(server, port)
    sample_data = b"x" * (1024 * 1024)
    headers = {
        "Content-type": "application/octet-stream",
    }

    start_time = time.time()
    conn.request(method=HTTPRequestMethod.post, url=path, body=sample_data, headers=headers)
    response = conn.getresponse()
    response.read()
    end_time = time.time()

    elapsed_time = end_time - start_time
    upload_speed_mbps = len(sample_data) / (elapsed_time * 1024 * 1024)
    conn.close()

    if file_size_mb:
        return file_size_mb / upload_speed_mbps
    else:
        return upload_speed_mbps


def parse_response(response: Response, extra: dict | None = None) -> ApiResponse:
    """
    Parse the response and return an ApiResponse object with the parsed data
    :param response:
    :param extra:
    :return:
    """
    try:
        json_response = response.json()
    except JSONDecodeError:
        json_response = {}

    return ApiResponse(
        status_code=response.status_code,
        message=response.reason,
        json_data=json_response,
        text_data=response.text,
        reason=response.reason,
        headers=response.headers,
        raw=response.raw,
        extra=extra,
    )
