import threading
import time

import requests

API_URL = "http://127.0.0.1:8000/api/v1/screener?min_roe=15"


def make_request(results, index):
    start_time = time.perf_counter()

    try:
        response = requests.get(API_URL, timeout=10)
        response_time = time.perf_counter() - start_time

        results[index] = {
            "status_code": response.status_code,
            "response_time": response_time,
        }

    except Exception as error:  # noqa: BLE001
        response_time = time.perf_counter() - start_time

        results[index] = {
            "status_code": None,
            "response_time": response_time,
            "error": str(error),
        }


def test_screener_load():
    results = [None] * 10
    threads = []

    start_time = time.perf_counter()

    for index in range(10):
        thread = threading.Thread(
            target=make_request,
            args=(results, index),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_time = time.perf_counter() - start_time

    print(f"\nTotal time for 10 concurrent requests: {total_time:.3f} seconds")

    for index, result in enumerate(results, start=1):
        print(
            f"Request {index}: "
            f"status={result['status_code']}, "
            f"time={result['response_time']:.3f} seconds"
        )

    assert all(result["status_code"] == 200 for result in results)
    assert total_time < 10
