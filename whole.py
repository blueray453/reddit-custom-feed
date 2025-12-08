from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import json
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

PROFILE_PATH = "/home/ismail/.mozilla/firefox/qrtlleto.default-esr"
USERNAME = "x_implement"
SUBREDDIT_IDS_FILE = "subreddit_ids.json"

FEEDS_DATA = {
    "Books": [
        "52book", "bookbinding", "bookclub", "bookporn", "booksuggestions", "childrensbooks", "FreeEBOOKS", "indesign",
        "librarians", "nonfictionbookclub", "nonfictionbooks", "nonfictionwriting", "printmaking", "whatsthatbook"
    ],
    "Business": [
        "advertising", "BehavioralEconomics", "business", "careeradvice", "careerguidance", "Economics", "economy",
        "Entrepreneur", "EntrepreneurRideAlong", "finance", "freelance", "juststart", "marketing", "negotiation",
        "options", "personalfinance", "ProductManagement", "RecruitCS", "recruiting", "recruitinghell", "sales",
        "slavelabour", "smallbusiness", "startups", "tax"
    ],
    "BusinessHR":
    ["ASkHR", "BehaviorAnalysis", "behaviordesign", "humanresources", "PersonalityPsychology", "psychometrics"],
    "BusinessOnline": [
        "adops", "bigseo", "Blogging", "content_marketing", "copywriting", "digital_marketing", "ecommerce", "PPC",
        "SEO", "SEO_Digital_Marketing", "SEO_Infographics", "shopify", "socialmedia", "TechSEO", "webmarketing"
    ],
    "DataScienceMathStat": [
        "Analyst", "analytics", "APStudents", "artificial", "ArtificialInteligence", "AskStatistics",
        "businessanalysis", "BusinessIntelligence", "compsci", "computerscience", "ComputerSciStudents", "cs50",
        "cscareerquestions", "data", "dataengineering", "DataHoarder", "dataisbeautiful", "dataisugly", "datascience",
        "datasciencenews", "datasets", "learnmachinelearning", "learnmath", "LocalLLM", "LocalLLaMA",
        "MachineLearning", "math", "mathematics", "mathmemes", "opendata", "rstats", "SampleSize", "singularity",
        "statistics", "tableau"
    ],
    "DesignUIUX": [
        "Art", "ArtPorn", "assholedesign", "computergraphics", "conceptart", "CrappyDesign", "Design",
        "design_critiques", "designfreebie", "designinspire", "DesignPorn", "drawing", "edmproduction",
        "graphic_design", "identifythisfont", "Illustration", "IllustratorTuts", "logodesign", "MaterialDesign",
        "photoshop", "typography", "UI_Design", "userexperience", "UXDesign", "UXResearch", "web_design"
    ],
    "Education": [
        "education", "highereducation", "instructionaldesign", "PhD", "ScienceTeachers", "Teachers", "teaching",
        "Training"
    ],
    "Electronics": [
        "arduino", "ArduinoProjects", "AskElectronics", "CircuitBending", "diyelectronics", "ECE",
        "ElectricalEngineering", "ElectronicComponents", "electronics", "embedded", "mathpics", "pihole",
        "PrintedCircuitBoard", "raspberry_pi", "RASPBERRY_PI_PROJECTS", "raspberrypi", "rfelectronics", "robotics"
    ],
    "News": ["news", "politics", "worldnews"],
    "PrivacyPiracyFreeSpeech": [
        "BitChute", "brave_browser", "cardano", "darknetplan", "DecentralizedApps", "deepweb", "dtube", "duckduckgo",
        "eos", "ethdev", "ethereum", "europrivacy", "firefox", "omise_go", "onions", "opendirectories", "Piracy",
        "PiratePets", "privacy", "privacytoolsIO", "signal", "tails", "thepiratebay", "TOR", "torrents", "tutanota",
        "xmrtrader"
    ],
    "Psychology": ["AcademicPsychology", "askpsychology", "psychology", "psychologyresearch", "psychologystudents"],
    "Security": [
        "AskNetsec", "cissp", "computerforensics", "cybersecurity", "HackBloc", "hacking", "HowToHack", "masterhacker",
        "netsec", "netsec_news", "netsecstudents", "SecurityAnalysis"
    ],
    "SelfDevelopment": [
        "confidence", "declutter", "findapath", "getdisciplined", "howtonotgiveafuck", "productivity", "quotes",
        "selfhelp", "selfimprovement", "sociology", "ted", "transhumanism", "zen"
    ],
    "ThoughtProvoking": [
        "AskReddit", "dankmemes", "HolUp", "HumansBeingBros", "interestingasfuck", "LifeProTips", "memes",
        "nextfuckinglevel", "savedyouaclick", "Showerthoughts", "todayilearned", "UpliftingNews", "Whatcouldgowrong",
        "wholesomememes", "WinStupidPrizes", "youseeingthisshit", "YouShouldKnow"
    ],
    "Software&WebDev&DevOps": [
        "algorithms", "datastructures", "devops", "docker", "Frontend", "ProgrammerHumor", "programming",
        "programmingcirclejerk", "programminghorror", "webdev", "ansible", "aws", "kubernetes"
    ],
    "SysAdmin&Linux&FOSS": [
        "debian", "Fuchsia", "iiiiiiitttttttttttt", "linux", "linuxmemes", "linuxmint", "opensource", "selfhosted",
        "sysadmin", "Sysadminhumor", "talesfromcallcenters", "talesfromsecurity", "talesfromtechsupport",
        "TalesFromTheCustomer", "TalesFromTheFrontDesk", "TalesFromYourServer", "Ubuntu"
    ],
    "SecurityBreaches": ["databreach", "DataBreaches", "pwned"]
}

# ============================================================================
# SELENIUM DRIVER SETUP
# ============================================================================

def initialize_driver():
    """Initialize and return a Firefox WebDriver with the specified profile."""
    options = Options()
    options.profile = PROFILE_PATH
    driver = webdriver.Firefox(options=options)
    return driver

# ============================================================================
# SUBREDDIT ID COLLECTION
# ============================================================================

def get_all_unique_subreddits(feeds_data):
    """Extract all unique subreddit names from feeds_data."""
    all_subreddits = set()
    for subs in feeds_data.values():
        all_subreddits.update(subs)
    return all_subreddits

def load_subreddit_ids_from_file(filepath):
    """Load subreddit IDs from JSON file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, 'r') as f:
            subreddit_ids = json.load(f)
        print(f"✅ Loaded {len(subreddit_ids)} subreddit IDs from file\n")
        return subreddit_ids
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return {}

def save_subreddit_ids_to_file(subreddit_ids, filepath):
    """Save subreddit IDs to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(subreddit_ids, f, indent=2)
    print(f"💾 Saved {len(subreddit_ids)} IDs to {filepath}")

def scrape_subreddit_id(driver, subreddit_name):
    """
    Scrape the subreddit ID (t5_xxxxx) for a given subreddit.
    Returns the ID if found, None otherwise.
    """
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/"
        driver.get(url)
        time.sleep(2)

        subreddit_id = None

        # Method 1: Look for header buttons
        try:
            header_buttons = driver.find_elements(By.CSS_SELECTOR, "shreddit-subreddit-header-buttons")
            for elem in header_buttons:
                sid = elem.get_attribute("subreddit-id")
                if sid and sid.startswith("t5_"):
                    subreddit_id = sid
                    break
        except Exception:
            pass

        # Method 2: Look in page source
        if not subreddit_id:
            page_source = driver.page_source
            if 'subreddit-id="' in page_source:
                start = page_source.find('subreddit-id="')
                if start != -1:
                    start += len('subreddit-id="')
                    end = page_source.find('"', start)
                    subreddit_id = page_source[start:end]

        # Method 3: Look for any element with subreddit-id attribute
        if not subreddit_id:
            elements = driver.find_elements(By.XPATH, '//*[@subreddit-id]')
            for elem in elements:
                sid = elem.get_attribute('subreddit-id')
                if sid and sid.startswith('t5_'):
                    subreddit_id = sid
                    break

        return subreddit_id

    except Exception as e:
        print(f"  ❌ Failed to scrape {subreddit_name}: {str(e)[:100]}")
        return None

def collect_missing_subreddit_ids(driver, missing_subreddits, existing_ids):
    """
    Scrape IDs for missing subreddits and add them to existing_ids dict.
    Returns the updated dictionary.
    """
    print(f"📥 Collecting {len(missing_subreddits)} missing subreddit IDs...\n")

    for sub in sorted(missing_subreddits):
        subreddit_id = scrape_subreddit_id(driver, sub)

        if subreddit_id:
            existing_ids[sub] = subreddit_id
            print(f"  ✅ {sub}: {subreddit_id}")
        else:
            print(f"  ❌ {sub}: ID not found")

        time.sleep(1)

    return existing_ids

def ensure_all_subreddit_ids(driver, all_subreddits, filepath):
    """
    Load existing subreddit IDs from file, collect any missing ones,
    and save the complete list back to file.
    """
    print(f"🔍 Total unique subreddits needed: {len(all_subreddits)}\n")

    # Load existing IDs
    subreddit_ids = load_subreddit_ids_from_file(filepath)

    # Find missing subreddits
    missing_subs = all_subreddits - set(subreddit_ids.keys())

    # Collect missing IDs if any
    if missing_subs:
        print(f"⚠️  Found {len(missing_subs)} missing subreddits\n")
        subreddit_ids = collect_missing_subreddit_ids(driver, missing_subs, subreddit_ids)
        save_subreddit_ids_to_file(subreddit_ids, filepath)

    print(f"\n📊 Total IDs available: {len(subreddit_ids)} out of {len(all_subreddits)}\n")
    return subreddit_ids

# ============================================================================
# CSRF TOKEN
# ============================================================================

def get_csrf_token(driver):
    """Extract CSRF token from Reddit page."""
    driver.get("https://www.reddit.com/")
    time.sleep(3)

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

    print(f"🔑 CSRF Token: {csrf_token}\n")

    if not csrf_token:
        raise Exception("Could not find CSRF token!")

    return csrf_token

# ============================================================================
# FEED MANAGEMENT
# ============================================================================

def generate_feed_slug(display_name):
    """Convert display name to URL slug (lowercase, no spaces/ampersands)."""
    return display_name.lower().replace('&', '').replace(' ', '')

def delete_custom_feed(driver, username, feed_name, csrf_token):
    """Delete a custom feed by name. Returns True if successful."""
    feed_label = f"/user/{username}/m/{feed_name}/"

    try:
        delete_result = driver.execute_script(
            """
            const payload = {
                operation: "CustomFeedDelete",
                variables: {
                    input: {
                        label: arguments[0]
                    }
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
        """, feed_label, csrf_token)

        if 'error' in delete_result:
            print(f"  ❌ {feed_name}: ERROR - {delete_result['error']}")
            return False
        elif delete_result['status'] == 200:
            print(f"  ✅ Deleted: {feed_name}")
            return True
        else:
            print(f"  ⚠️  {feed_name}: {delete_result['status']} {delete_result['statusText']}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to delete {feed_name}: {e}")
        return False

def delete_all_existing_feeds(driver, username, feeds_data, csrf_token):
    """Delete all existing custom feeds based on feeds_data keys."""
    existing_feeds = [generate_feed_slug(feed_name) for feed_name in feeds_data.keys()]

    print(f"{'='*60}")
    print(f"🗑️  Deleting {len(existing_feeds)} existing custom feeds...")
    print(f"{'='*60}\n")

    deleted_count = 0
    failed_count = 0

    for feed_name in existing_feeds:
        if delete_custom_feed(driver, username, feed_name, csrf_token):
            deleted_count += 1
        else:
            failed_count += 1
        time.sleep(1)

    print(f"\n✅ Deletion complete: {deleted_count} deleted, {failed_count} failed\n")
    time.sleep(2)

def create_feed_with_all_subreddits(driver, display_name, subreddit_ids, csrf_token):
    """
    APPROACH 1: Create feed with all subreddits in one request (faster but sometimes fails).
    Returns True if successful, False otherwise.
    """
    print(f"📝 Approach 1: Creating feed with all subreddits at once...")

    create_result = driver.execute_script(
        """
        const payload = {
            operation: "CustomFeedCreate",
            variables: {
                input: {
                    displayName: arguments[0],
                    descriptionMd: "",
                    visibility: "PUBLIC",
                    subredditIds: arguments[1]
                }
            },
            csrf_token: arguments[2]
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
    """, display_name, subreddit_ids, csrf_token)

    # Check if creation succeeded
    if 'error' in create_result:
        print(f"⚠️  Approach 1 failed with error: {create_result['error']}")
        return False
    elif create_result['status'] != 200:
        print(f"⚠️  Approach 1 failed: {create_result['status']} {create_result['statusText']}")
        return False

    response_data = create_result.get('data', {})
    if isinstance(response_data, dict):
        errors = response_data.get('errors', [])
        create_data = response_data.get('data', {})

        if errors or (create_data and create_data.get('createMultireddit') is None):
            print(f"⚠️  Approach 1 failed - Reddit returned errors")
            if errors:
                print(f"   Error details: {errors[0].get('message', 'Unknown error')[:100]}")
            return False
        else:
            print(f"✅ Approach 1 succeeded - Feed created with all subreddits!")
            return True

    return False

def create_empty_feed(driver, display_name, csrf_token):
    """Create an empty custom feed. Returns True if successful."""
    create_result = driver.execute_script(
        """
        const payload = {
            operation: "CustomFeedCreate",
            variables: {
                input: {
                    displayName: arguments[0],
                    descriptionMd: "",
                    visibility: "PUBLIC",
                    subredditIds: []
                }
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
    """, display_name, csrf_token)

    if 'error' in create_result:
        print(f"❌ ERROR creating empty feed: {create_result['error']}")
        return False
    elif create_result['status'] != 200:
        print(f"❌ Failed to create empty feed: {create_result['status']}")
        return False

    response_data = create_result.get('data', {})
    if isinstance(response_data, dict):
        errors = response_data.get('errors', [])
        create_data = response_data.get('data', {})

        if errors or (create_data and create_data.get('createMultireddit') is None):
            print(f"❌ Empty feed creation failed!")
            if errors:
                print(f"   Reddit errors: {json.dumps(errors, indent=2)}")
            return False

    print(f"✅ Empty feed created successfully!")
    return True

def add_subreddit_to_feed(driver, username, feed_slug, subreddit_id, csrf_token):
    """Add a single subreddit to a feed. Returns True if successful."""
    feed_label = f"/user/{username}/m/{feed_slug}/"

    add_result = driver.execute_script(
        """
        const label = arguments[0];
        const subredditId = arguments[1];
        const csrf_token = arguments[2];

        const payload = {
            operation: "CustomFeedAddSubreddits",
            variables: { label: label, subredditIds: [subredditId] },
            csrf_token: csrf_token
        };

        return fetch('/svc/shreddit/graphql', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        })
        .then(response => response.text().then(text => {
            let data;
            try { data = JSON.parse(text); }
            catch (e) { data = text.slice(0,500); }
            return { status: response.status, statusText: response.statusText, data: data };
        }))
        .catch(error => ({ error: error.toString() }));
    """, feed_label, subreddit_id, csrf_token)

    result_data = {}
    if isinstance(add_result, dict):
        data_field = add_result.get("data", {})
        if isinstance(data_field, dict):
            result_data = data_field.get("data", {}).get("addSubredditsToMultireddit", {})

    return isinstance(result_data, dict) and result_data.get("ok", False)

def add_subreddits_to_feed(driver, username, feed_slug, subreddit_ids, csrf_token):
    """Add multiple subreddits to a feed one by one."""
    if len(subreddit_ids) == 0:
        return True

    print(f"📚 Adding {len(subreddit_ids)} subreddits...")

    success_count = 0
    for sid in subreddit_ids:
        if add_subreddit_to_feed(driver, username, feed_slug, sid, csrf_token):
            print(f"  ✅ Added {sid}")
            success_count += 1
        else:
            print(f"  ❌ Failed to add {sid}")
        time.sleep(0.5)

    print(f"✅ Added {success_count}/{len(subreddit_ids)} subreddits")
    return success_count == len(subreddit_ids)

def create_feed_empty_then_add(driver, username, display_name, subreddit_ids, csrf_token):
    """
    APPROACH 2: Create empty feed then add subreddits one by one (slower but more reliable).
    Returns True if successful.
    """
    print(f"\n📝 Approach 2: Creating empty feed then adding subreddits...")

    feed_slug = generate_feed_slug(display_name)
    feed_label = f"/user/{username}/m/{feed_slug}/"

    # Create empty feed
    if not create_empty_feed(driver, display_name, csrf_token):
        return False

    # Navigate to the feed page before adding subreddits
    feed_url = f"https://www.reddit.com{feed_label}"
    print(f"🔄 Navigating to {feed_url}...")
    driver.get(feed_url)
    time.sleep(3)

    # Add subreddits
    if len(subreddit_ids) > 0:
        success = add_subreddits_to_feed(driver, username, feed_slug, subreddit_ids, csrf_token)
        if success:
            print(f"✅ Approach 2 succeeded - All {len(subreddit_ids)} subreddits added!")
        else:
            print(f"⚠️  Approach 2 partial success - Some subreddits failed to add")
        return success

    return True

def create_feed_with_subreddits(driver, username, display_name, subreddit_ids, csrf_token):
    """
    Create a custom feed and populate it with subreddits.
    Tries Approach 1 (fast) first, falls back to Approach 2 (reliable) if it fails.
    """
    feed_slug = generate_feed_slug(display_name)
    feed_label = f"/user/{username}/m/{feed_slug}/"

    print(f"\n{'='*60}")
    print(f"📝 Creating feed: {display_name}")
    print(f"{'='*60}")
    print(f"📚 Total subreddits: {len(subreddit_ids)}")

    # APPROACH 1: Try creating feed with all subreddits at once (faster)
    if create_feed_with_all_subreddits(driver, display_name, subreddit_ids, csrf_token):
        print(f"✅ Feed URL: https://www.reddit.com{feed_label}")
        return True

    # APPROACH 2: If Approach 1 failed, create empty feed then add subreddits
    if create_feed_empty_then_add(driver, username, display_name, subreddit_ids, csrf_token):
        print(f"✅ Feed URL: https://www.reddit.com{feed_label}")
        return True

    print(f"❌ Failed to create feed: {display_name}")
    return False

def create_all_feeds(driver, username, feeds_data, subreddit_ids, csrf_token):
    """Create all custom feeds from feeds_data."""
    print(f"{'='*60}")
    print(f"📝 Creating {len(feeds_data)} new custom feeds...")
    print(f"{'='*60}\n")

    for feed_display_name, subreddits in feeds_data.items():
        # Get subreddit IDs for this feed
        feed_subreddit_ids = []
        missing_subs = []

        for sub_name in subreddits:
            if sub_name in subreddit_ids:
                feed_subreddit_ids.append(subreddit_ids[sub_name])
            else:
                missing_subs.append(sub_name)

        if missing_subs:
            print(f"⚠️  Missing IDs for: {', '.join(missing_subs)}")

        # Create the feed
        create_feed_with_subreddits(driver, username, feed_display_name, feed_subreddit_ids, csrf_token)

        time.sleep(2)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Initialize driver
    driver = initialize_driver()

    try:
        # Step 1: Ensure all subreddit IDs are collected
        all_subreddits = get_all_unique_subreddits(FEEDS_DATA)
        subreddit_ids = ensure_all_subreddit_ids(driver, all_subreddits, SUBREDDIT_IDS_FILE)

        # Step 2: Get CSRF token
        csrf_token = get_csrf_token(driver)

        # Step 3: Delete existing feeds
        delete_all_existing_feeds(driver, USERNAME, FEEDS_DATA, csrf_token)

        # Step 4: Create all new feeds
        create_all_feeds(driver, USERNAME, FEEDS_DATA, subreddit_ids, csrf_token)

        print(f"\n🎉 All feeds processed! Visit https://www.reddit.com/user/{USERNAME}/")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
