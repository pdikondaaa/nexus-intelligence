import requests
import json
import traceback

access_token = "YOUR_ACCESS_TOKEN_HERE"
latest_query = "leave policy"
sp_site = "https://alignedautomation.sharepoint.com/sites/Nexus"
query_text = f'{latest_query} path:"{sp_site}"'
sp_search_url = f"{sp_site}/_api/search/query?querytext='{query_text}'"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json;odata=nometadata"
}

try:
    sp_response = requests.get(sp_search_url, headers=headers)
    print("STATUS", sp_response.status_code)
    results = sp_response.json()
    
    # robust parsing
    if "d" in results and "query" in results["d"]:
        results = results["d"]["query"]
    
    rows = results.get("PrimaryQueryResult", {}).get("RelevantResults", {}).get("Table", {}).get("Rows", [])
    if isinstance(rows, dict) and "results" in rows:
        rows = rows["results"]
        
    print(f"Num rows parsed: {len(rows)}")
    
    for row in rows[:1]:
        cells = row.get("Cells", [])
        if isinstance(cells, dict) and "results" in cells:
            cells = cells["results"]
        print("CELLS in FIRST ROW:")
        print(len(cells))
except Exception as e:
    traceback.print_exc()

