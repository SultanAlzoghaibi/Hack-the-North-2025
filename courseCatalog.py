# courseCatalog.py
import requests, json, sys

HOST = "https://calendar.ucalgary.ca/graphql"

Q = """
query Courses($query: String!, $skip: Int!, $limit: Int!) {
  searchCourses(query: $query, skip: $skip, limit: $limit) {
    listLength
    data {
      code
      description
      subjectCode
      status
    }
  }
}
"""

HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://calendar.ucalgary.ca",
    "Referer": "https://calendar.ucalgary.ca/courses?subjectCode=CPSC&page=1&cq=",
    "User-Agent": "Mozilla/5.0"
}

def fetch_all():
    out = []
    skip, limit = 0, 100

    while True:
        body = {"query": Q, "variables": {"query": "CPSC", "skip": skip, "limit": limit}}
        resp = requests.post(HOST, headers=HEADERS, json=body, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        if "data" not in payload or not payload["data"]:
            print("Unexpected response:", json.dumps(payload)[:300], file=sys.stderr)
            break

        block = payload["data"]["searchCourses"]
        items = block.get("data", [])
        for i in items:
            if i.get("subjectCode") == "CPSC" and i.get("status") == "Active":
                out.append({
                    "code": i.get("code", ""),
                    "description": (i.get("description") or "").strip()
                })

        skip += limit
        if skip >= block.get("listLength", 0):
            break

    with open("ucalgary_cpsc_courses.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(out)} CPSC courses to ucalgary_cpsc_courses.json")

if __name__ == "__main__":
    fetch_all()