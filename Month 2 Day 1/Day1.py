import requests
from pprint import pprint

response = requests.get("https://httpbin.org/get")
print(response.status_code)   # 200
pprint(response.json())        # parsed response body
print(type(response))
pprint(response)



# requests.get("https://httpbin.org/get")
# requests.post("https://httpbin.org/post", json={"name": "Alice"})
# requests.put("https://httpbin.org/put", json={"name": "Alice", "age": 30})
# requests.patch("https://httpbin.org/patch", json={"age": 31})
# requests.delete("https://httpbin.org/delete")

# Status codes
response = requests.get("https://httpbin.org/status/404")
print(response.status_code)   # 404

"""
Status codes — memorize the ranges, then the classics
The first digit tells you the category:

2xx — success. 200 OK, 201 Created (after a successful POST), 204 No Content (success, nothing to return).
3xx — redirect. 301 Moved Permanently, 304 Not Modified (cached version is still fine).
4xx — you (the client) messed up. 400 Bad Request, 401 Unauthorized (no/bad credentials), 403 Forbidden (credentials fine, not allowed), 404 Not Found, 429 Too Many Requests.
5xx — the server messed up. 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable.

"""

r = requests.get("https://httpbin.org/status/404")
print(r.status_code)          # 404
print(r.ok)                   # False — .ok is True only for 2xx

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer fake-token-123",
    "Accept": "application/json",
}
response = requests.get("https://httpbin.org/headers", headers=headers)
pprint(response.json())   # httpbin echoes back exactly what it received