import requests

url = "https://i.redd.it/xwkw3mdy516g1.jpeg"

# Pretend to be a normal script, not a browser
headers = {
    "User-Agent": "curl/8.0",
}

r = requests.get(url, headers=headers)

if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
    with open("image.jpeg", "wb") as f:
        f.write(r.content)
    print("Saved as image.jpeg")
else:
    print("Reddit returned:", r.status_code, r.headers.get("Content-Type"))
