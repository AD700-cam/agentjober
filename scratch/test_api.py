import httpx

print("Testing RemoteOK API...")
r = httpx.get("https://remoteok.com/api", headers={"User-Agent": "Mozilla/5.0"}, timeout=15.0, follow_redirects=True)
data = r.json()
print(f"Status: {r.status_code}, Total Jobs: {len(data)-1}")
print()

# Show first 5 jobs
for j in data[1:6]:
    pos = j.get("position", "?")
    comp = j.get("company", "?")
    tags = j.get("tags", [])
    url = j.get("url", "")
    print(f"  {pos} @ {comp}")
    print(f"    Tags: {', '.join(tags[:5])}")
    print(f"    URL: {url}")
    print()

# Check how many match our tech stack
relevant_tags = ["react", "nextjs", "typescript", "javascript", "frontend", "fullstack", "node", "developer", "engineer", "web"]
matched = 0
for j in data[1:]:
    combined = f"{j.get('position','')} {' '.join(j.get('tags',[]))}".lower()
    if any(t in combined for t in relevant_tags):
        matched += 1

print(f"Relevant to our tech stack: {matched} jobs")
