import requests
import time
import collections
from multiprocessing import Pool, cpu_count

# Configuration
# The server's public IP address
BASE_URL = "http://72.60.221.150:8080"
STUDENT_ID = "MDS202508"  # Replace with your actual student ID

def login(student_id):
    response = requests.post(BASE_URL + "/login", json = {"student_id": student_id})
    response.raise_for_status()
    return response.json()["secret_key"]

def mapper(filename_chunk):
    secret_key = login(STUDENT_ID)
    counts = collections.Counter()

    for filename in filename_chunk:
        title = get_publication_title(secret_key, filename)
        if title:
            first_word = title.strip().split()[0] if title.strip() else None
            if first_word:
                counts[first_word] += 1
    return counts

def get_publication_title(secret_key, filename):
    max_retries = 8
    wait = 0.5

    for attempt in range(max_retries):
        try:
            response = requests.post(BASE_URL + "/lookup", json = {"secret_key": secret_key, "filename": filename},timeout = 10)
            if response.status_code == 429:
                print(f"[429] Rate Limited on {filename}, waiting {wait:.1f}s...")
                time.sleep(wait)
                wait *= 2
                continue
            response.raise_for_status()
            return response.json().get("title", "")
        except requests.RequestException as e:
            print(f"[ERROR] {filename} attempt {attempt+1}: {e}")
            time.sleep(wait)
            wait *= 2
    print(f"[FAILED] Giving up on {filename} after {max_retries} attempts.")
    return None


def verify_top_10(student_id, top_10_list):
    secret_key = login(student_id)
    response = requests.post(f"{BASE_URL}/verify", json = {"secret_key": secret_key, "top_10": top_10_list})
    response.raise_for_status()
    result = response.json()
    print(f"\n=== Verification Result ===")
    print(f"Score   : {result.get('score')} / {result.get('total')}")
    print(f"Correct : {result.get('correct')}")
    print(f"Message : {result.get('message')}")
    return result

if __name__ == "__main__":
    all_filenames = [f"pub_{i}.txt" for i in range(1000)]

    num_workers = min(cpu_count(), 10)
    chunk_size = len(all_filenames) // num_workers
    chunks = [
        all_filenames[i * chunk_size: (i + 1) * chunk_size]
        for i in range(num_workers)
    ]

    remainder = all_filenames[num_workers * chunk_size:]
    if remainder:
        chunks[-1].extend(remainder)

    print(f"Launching {num_workers} workers, ~{chunk_size} files each...\n")

    with Pool(processes=num_workers) as pool:
        partial_counts = pool.map(mapper, chunks)

    total_counts = collections.Counter()
    for partial in partial_counts:
        total_counts += partial

    top_10 = [word for word, _ in total_counts.most_common(10)]

    print(f"\nTop 10 most frequent first words:")
    for rank, (word, count) in enumerate(total_counts.most_common(10), 1):
        print(f"  {rank:>2}. {word:<20} ({count} occurrences)")

    verify_top_10(STUDENT_ID, top_10)

