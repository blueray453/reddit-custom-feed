from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import json

profile_path = "/home/ismail/.mozilla/firefox/qrtlleto.default-esr"
options = Options()
options.profile = profile_path
driver = webdriver.Firefox(options=options)

# Subreddit IDs we collected
subreddit_ids = {
    "52book": "t5_2s935",
    "bookbinding": "t5_2x40k",
    "bookclub": "t5_2qktu",
    "booklists": "t5_2se0c",
    "bookporn": "t5_2sa5v",
    "booksuggestions": "t5_3157y",
    "childrensbooks": "t5_2ryh7",
    "FreeEBOOKS": "t5_2r61s",
    "indesign": "t5_2rmwz",
    "librarians": "t5_2qpf2",
    "nonfictionbookclub": "t5_38sv3",
    "nonfictionbooks": "t5_2xd5n",
    "nonfictionwriting": "t5_2utv5",
    "printmaking": "t5_2ry2d",
    "whatsthatbook": "t5_2w9c6"
}

feed_url = "https://www.reddit.com/user/x_implement/m/books/"
driver.get(feed_url)
time.sleep(3)  # Wait for page to load

# Get CSRF token from the page
csrf_token = driver.execute_script("""
    var csrf_token = null;
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        if (cookie.trim().startsWith('csrf_token=')) {
            csrf_token = cookie.split('=')[1];
            break;
        }
    }

    if (!csrf_token) {
        const scripts = document.getElementsByTagName('script');
        for (let script of scripts) {
            if (script.textContent.includes('csrf_token')) {
                const match = script.textContent.match(/"csrf_token":"([^"]+)"/);
                if (match) {
                    csrf_token = match[1];
                    break;
                }
            }
        }
    }

    return csrf_token;
""")

print(f"CSRF Token: {csrf_token}")

if not csrf_token:
    print("ERROR: Could not find CSRF token!")
    driver.quit()
    exit(1)

# Add each subreddit using JavaScript fetch
for sub_name, sub_id in subreddit_ids.items():
    try:
        result = driver.execute_script(
            """
            const payload = {
                operation: "CustomFeedAddSubreddits",
                variables: {
                    label: "/user/x_implement/m/books/",
                    subredditIds: [arguments[0]]
                },
                csrf_token: arguments[1]
            };

            return fetch('/svc/shreddit/graphql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
                credentials: 'include'
            })
            .then(response => {
                return response.text().then(text => {
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        data = text.substring(0, 500);
                    }
                    return {
                        status: response.status,
                        statusText: response.statusText,
                        data: data
                    };
                });
            })
            .catch(error => ({
                error: error.toString()
            }));
        """, sub_id, csrf_token)

        if 'error' in result:
            print(f"{sub_name} ({sub_id}): ERROR - {result['error']}")
        else:
            status_emoji = "✅" if result['status'] == 200 else "❌"
            print(f"{status_emoji} {sub_name} ({sub_id}): {result['status']} {result['statusText']}")
            if result['status'] != 200:
                print(f"  Response: {json.dumps(result['data'])[:200]}")

        time.sleep(1)  # Be nice to Reddit's servers

    except Exception as e:
        print(f"Failed to add {sub_name}: {e}")

driver.quit()
print("\n✅ Done!")
