import time
import requests
import statistics

BASE_URL = "http://localhost:8000"

def benchmark_search_api(num_requests: int = 20):
    print("=" * 60)
    print(f"🚀 BẮT ĐẦU BENCHMARK VECTOR SEARCH API ({num_requests} requests)")
    print("=" * 60)

    url = f"{BASE_URL}/api/v1/documents/search"
    payload = {
        "query": "DeepSeek-V3.2 performance and model architecture",
        "top_k": 5
    }

    latencies = []
    success_count = 0

    for i in range(num_requests):
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, timeout=10.0)
            elapsed = (time.time() - start_time) * 1000  # Đổi sang miligiây (ms)
            if response.status_code == 200:
                latencies.append(elapsed)
                success_count += 1
                print(f"  Req #{i+1:02d}: Status 200 OK | Latency: {elapsed:.2f} ms")
            else:
                print(f"  Req #{i+1:02d}: Status {response.status_code}")
        except Exception as e:
            print(f"  Req #{i+1:02d}: Failed ({e})")

    if latencies:
        avg_latency = statistics.mean(latencies)
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99 = max(latencies)

        print("\n📊 BÁO CÁO THỐNG KÊ HIỆU NĂNG VECTOR SEARCH:")
        print("-" * 60)
        print(f"  - Thành công:               {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
        print(f"  - Trung bình (Avg Latency): {avg_latency:.2f} ms")
        print(f"  - P50 (Median Latency):     {p50:.2f} ms")
        print(f"  - P95 Latency:              {p95:.2f} ms")
        print(f"  - P99 Latency:              {p99:.2f} ms")
        print(f"  - Throughput (Tốc độ):      {num_requests / (sum(latencies)/1000):.2f} req/sec")
        print("-" * 60)

if __name__ == "__main__":
    benchmark_search_api(num_requests=20)