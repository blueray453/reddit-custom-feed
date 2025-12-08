from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
import time
import json
import argparse
import sys

# ============================================================================
# CONFIGURATION PRESETS
# ============================================================================

PRESETS = {
    'default': {
        'methods': ['POST'],
        'url_patterns': ['graphql', '/api/'],
        'exclude_patterns': ['events', 'analytics', 'track'],
        'capture_headers': False,
        'capture_timing': True,
        'max_body_length': 2000,
    },
    'all': {
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        'url_patterns': [''],
        'exclude_patterns': ['events', 'analytics', 'track'],
        'capture_headers': True,
        'capture_timing': True,
        'max_body_length': 2000,
    },
    'errors': {
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        'url_patterns': [''],
        'exclude_patterns': [],
        'capture_headers': True,
        'capture_timing': True,
        'max_body_length': 2000,
        'only_errors': True,  # Special flag
    },
    'get-only': {
        'methods': ['GET'],
        'url_patterns': ['/api/', 'graphql'],
        'exclude_patterns': ['events', 'analytics'],
        'capture_headers': False,
        'capture_timing': True,
        'max_body_length': 500,
    },
    'minimal': {
        'methods': ['POST'],
        'url_patterns': ['graphql'],
        'exclude_patterns': ['events', 'analytics', 'track'],
        'capture_headers': False,
        'capture_timing': False,
        'max_body_length': 1000,
    },
    'verbose': {
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        'url_patterns': [''],
        'exclude_patterns': [],
        'capture_headers': True,
        'capture_timing': True,
        'max_body_length': 5000,
    },
}

PROFILE_PATH = "/home/ismail/.mozilla/firefox/qrtlleto.default-esr"

# ============================================================================
# COMMAND LINE ARGUMENT PARSER
# ============================================================================

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(
        description='Reddit Network Stream Monitor - Capture and display network requests in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CONFIGURATION PRESETS:
  default       - Only POST requests to GraphQL/API (default)
  all           - All HTTP methods, all URLs (with headers)
  errors        - Only failed requests (4xx, 5xx status codes)
  get-only      - Only GET requests to API endpoints
  minimal       - Only GraphQL POST requests (compact output)
  verbose       - Everything with full details

EXAMPLES:
  # Use default preset (POST requests only)
  python network_debugger.py

  # Monitor all requests
  python network_debugger.py --preset all

  # Only show failed requests
  python network_debugger.py --preset errors

  # Custom configuration
  python network_debugger.py --methods GET POST --url-pattern /api/ --no-headers

  # Start with specific URL
  python network_debugger.py --url https://old.reddit.com/

  # Auto-save to file
  python network_debugger.py --save requests.json

  # Quiet mode (less verbose output)
  python network_debugger.py --quiet

  # Show request numbers only (no bodies)
  python network_debugger.py --minimal

KEYBOARD SHORTCUTS:
  Ctrl+Q        - Stop monitoring and exit
  Ctrl+C        - Stop monitoring and exit
  Close Browser - Automatically stops and exits
        """)

    # Preset selection
    parser.add_argument('--preset',
                        '-p',
                        choices=list(PRESETS.keys()),
                        default='default',
                        help='Use a predefined configuration preset')

    # URL options
    parser.add_argument('--url',
                        '-u',
                        default='https://www.reddit.com/',
                        help='Starting URL (default: https://www.reddit.com/)')

    parser.add_argument('--profile', default=PROFILE_PATH, help=f'Firefox profile path (default: {PROFILE_PATH})')

    # Custom configuration options
    parser.add_argument('--methods',
                        '-m',
                        nargs='+',
                        choices=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
                        help='HTTP methods to capture (overrides preset)')

    parser.add_argument('--url-pattern', nargs='+', help='URL patterns to match (overrides preset)')

    parser.add_argument('--exclude', nargs='+', help='URL patterns to exclude (overrides preset)')

    parser.add_argument('--headers', action='store_true', help='Capture request/response headers')

    parser.add_argument('--no-headers', action='store_true', help='Do not capture headers')

    parser.add_argument('--no-timing', action='store_true', help='Do not capture timing information')

    parser.add_argument('--max-body', type=int, help='Maximum body length to display (in characters)')

    # Output options
    parser.add_argument('--save', metavar='FILENAME', help='Save captured requests to file on exit (no prompt)')

    parser.add_argument('--quiet',
                        '-q',
                        action='store_true',
                        help='Quiet mode - only show request headers, not bodies')

    parser.add_argument('--minimal', action='store_true', help='Minimal mode - only show request numbers and URLs')

    parser.add_argument('--check-interval',
                        type=float,
                        default=0.5,
                        help='How often to check for new requests (seconds, default: 0.5)')

    # List presets
    parser.add_argument('--list-presets', action='store_true', help='List all available presets and exit')

    return parser

def list_presets():
    """Display all available presets with their configurations."""
    print("\n" + "=" * 60)
    print("AVAILABLE PRESETS")
    print("=" * 60 + "\n")

    for name, config in PRESETS.items():
        print(f"📦 {name}")
        print(f"   Methods: {', '.join(config['methods'])}")
        print(f"   URL Patterns: {', '.join(config['url_patterns']) if config['url_patterns'] else 'All'}")
        print(f"   Exclude: {', '.join(config['exclude_patterns']) if config['exclude_patterns'] else 'None'}")
        print(f"   Headers: {'Yes' if config['capture_headers'] else 'No'}")
        print(f"   Timing: {'Yes' if config['capture_timing'] else 'No'}")
        print(f"   Max Body: {config['max_body_length']} chars")
        if config.get('only_errors'):
            print(f"   Special: Only show error responses")
        print()

def build_config_from_args(args):
    """Build configuration from command line arguments."""
    # Start with preset
    config = PRESETS[args.preset].copy()

    # Override with command line arguments
    if args.methods:
        config['methods'] = args.methods

    if args.url_pattern:
        config['url_patterns'] = args.url_pattern

    if args.exclude:
        config['exclude_patterns'] = args.exclude

    if args.headers:
        config['capture_headers'] = True

    if args.no_headers:
        config['capture_headers'] = False

    if args.no_timing:
        config['capture_timing'] = False

    if args.max_body:
        config['max_body_length'] = args.max_body

    # Add command line specific options
    config['quiet'] = args.quiet
    config['minimal'] = args.minimal
    config['save_file'] = args.save
    config['check_interval'] = args.check_interval

    return config

# ============================================================================
# SELENIUM DRIVER SETUP
# ============================================================================

def initialize_driver(profile_path):
    """Initialize and return a Firefox WebDriver with the specified profile."""
    options = Options()
    options.profile = profile_path
    driver = webdriver.Firefox(options=options)
    return driver

def is_driver_alive(driver):
    """Check if the WebDriver session is still active."""
    try:
        # Try to get the current URL - this will fail if browser is closed
        _ = driver.current_url
        return True
    except (WebDriverException, InvalidSessionIdException):
        return False

# ============================================================================
# ENHANCED NETWORK STREAM MONITOR
# ============================================================================

def install_enhanced_monitor(driver, config):
    """
    Install JavaScript to capture comprehensive network activity.
    """
    methods_list = json.dumps(config['methods'])
    url_patterns = json.dumps(config['url_patterns'])
    exclude_patterns = json.dumps(config['exclude_patterns'])
    capture_headers = 'true' if config['capture_headers'] else 'false'

    monitor_script = f"""
        // Store original fetch
        const originalFetch = window.fetch;
        window.capturedRequests = [];

        const METHODS_TO_CAPTURE = {methods_list};
        const URL_PATTERNS = {url_patterns};
        const EXCLUDE_PATTERNS = {exclude_patterns};
        const CAPTURE_HEADERS = {capture_headers};

        // Helper function to check if URL should be captured
        function shouldCapture(url, method) {{
            // Check if method matches
            if (!METHODS_TO_CAPTURE.includes(method)) return false;

            // If no patterns specified, capture all
            if (URL_PATTERNS.length === 0 || URL_PATTERNS[0] === '') return true;

            // Check if URL matches any pattern
            const matchesPattern = URL_PATTERNS.some(pattern => url.includes(pattern));
            if (!matchesPattern) return false;

            // Check if URL should be excluded
            const shouldExclude = EXCLUDE_PATTERNS.some(pattern => url.includes(pattern));
            if (shouldExclude) return false;

            return true;
        }}

        // Override fetch to capture requests AND responses
        window.fetch = function (...args) {{
            const [url, options = {{}}] = args;
            const method = options.method || 'GET';

            if (shouldCapture(url, method)) {{
                const startTime = performance.now();
                const requestId = Date.now() + Math.random();

                const requestData = {{
                    id: requestId,
                    url: url,
                    method: method,
                    timestamp: new Date().toISOString(),
                    body: null,
                    headers: null,
                    startTime: startTime
                }};

                // Capture request headers
                if (CAPTURE_HEADERS && options.headers) {{
                    requestData.headers = options.headers;
                }}

                // Parse request body
                if (options.body) {{
                    try {{
                        requestData.body = JSON.parse(options.body);
                    }} catch (e) {{
                        requestData.body = options.body;
                    }}
                }}

                // Call original fetch and capture response
                return originalFetch.apply(this, args).then(response => {{
                    const endTime = performance.now();
                    const clonedResponse = response.clone();

                    clonedResponse.text().then(responseBody => {{
                        const responseData = {{
                            id: requestId,
                            status: response.status,
                            statusText: response.statusText,
                            timestamp: new Date().toISOString(),
                            duration: Math.round(endTime - startTime),
                            body: null,
                            headers: null
                        }};

                        // Capture response headers
                        if (CAPTURE_HEADERS) {{
                            responseData.headers = {{}};
                            for (let [key, value] of response.headers.entries()) {{
                                responseData.headers[key] = value;
                            }}
                        }}

                        // Parse response body
                        try {{
                            responseData.body = JSON.parse(responseBody);
                        }} catch (e) {{
                            responseData.body = responseBody;
                        }}

                        // Store complete request-response pair
                        window.capturedRequests.push({{
                            request: requestData,
                            response: responseData
                        }});
                    }});

                    return response;
                }}).catch(error => {{
                    // Capture failed requests
                    const endTime = performance.now();
                    window.capturedRequests.push({{
                        request: requestData,
                        response: {{
                            error: error.toString(),
                            timestamp: new Date().toISOString(),
                            duration: Math.round(endTime - startTime)
                        }}
                    }});
                    throw error;
                }});
            }}

            // Call original fetch for non-monitored requests
            return originalFetch.apply(this, args);
        }};

        console.log('✅ Enhanced monitor installed');
        console.log('Capturing methods:', METHODS_TO_CAPTURE);
        console.log('URL patterns:', URL_PATTERNS);
    """

    driver.execute_script(monitor_script)

def save_captured_data(captured, filename):
    """Save captured data to file."""
    try:
        with open(filename, 'w') as f:
            json.dump(captured, f, indent=2)
        print(f"💾 Saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save file: {e}")
        return False

def stream_network_activity(driver, config):
    """
    Continuously stream network activity to console.
    """
    last_count = 0
    request_number = 0
    check_interval = config.get('check_interval', 0.5)
    captured = []
    browser_closed = False

    print("\n" + "=" * 50)
    print("🌊 STREAMING NETWORK ACTIVITY")
    print("=" * 50)
    print(f"Methods: {', '.join(config['methods'])}")
    patterns = ', '.join(config['url_patterns']) if config['url_patterns'] else 'All'
    print(f"Patterns: {patterns}")
    if config.get('quiet'):
        print("Mode: Quiet (headers only)")
    elif config.get('minimal'):
        print("Mode: Minimal (numbers and URLs only)")
    if config.get('save_file'):
        print(f"Will save to: {config['save_file']}")
    print("Press Ctrl+Q or Ctrl+C to stop (or just close the browser)\n")

    try:
        while True:
            # Check if browser is still alive
            if not is_driver_alive(driver):
                print("\n🚪 Browser closed by user")
                browser_closed = True
                break

            try:
                # Get captured requests
                captured = driver.execute_script("return window.capturedRequests || [];")

                # Print new requests
                if len(captured) > last_count:
                    for req_resp in captured[last_count:]:
                        # Filter for errors if preset is 'errors'
                        if config.get('only_errors'):
                            response = req_resp.get('response', {})
                            status = response.get('status', 0)
                            has_error = response.get('error') or (status >= 400)
                            if not has_error:
                                continue

                        request_number += 1

                        if config.get('minimal'):
                            print_minimal_request(req_resp, request_number)
                        elif config.get('quiet'):
                            print_quiet_request(req_resp, request_number, config)
                        else:
                            print_enhanced_request_response(req_resp, request_number, config)

                    last_count = len(captured)

            except (WebDriverException, InvalidSessionIdException):
                # Browser was closed
                print("\n🚪 Browser closed by user")
                browser_closed = True
                break

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user (Ctrl+C)")

    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: Captured {request_number} request/response pairs")
    print("=" * 50)

    # Save if --save was specified and we have data
    if config.get('save_file') and len(captured) > 0:
        save_captured_data(captured, config['save_file'])

def print_minimal_request(req_resp, request_number):
    """Print minimal request info - just number and URL."""
    request = req_resp.get('request', {})
    response = req_resp.get('response', {})

    method = request.get('method', 'N/A')
    url = request.get('url', 'N/A')
    status = response.get('status', 'N/A')
    duration = response.get('duration', 0)

    # Status icon
    if isinstance(status, int):
        if status >= 200 and status < 300:
            icon = "✅"
        elif status >= 400:
            icon = "❌"
        else:
            icon = "🔄"
    else:
        icon = "❓"

    print(f"{icon} #{request_number} {method} {status} ({duration}ms) {url}")

def print_quiet_request(req_resp, request_number, config):
    """Print request without bodies - only headers and metadata."""
    request = req_resp.get('request', {})
    response = req_resp.get('response', {})

    # Extract info
    full_url = request.get('url', 'N/A')
    short_url = full_url.split('/')[-1] if '/' in full_url else full_url
    if len(short_url) > 30:
        short_url = short_url[:30] + '...'

    timestamp = request.get('timestamp', 'N/A')
    if timestamp != 'N/A':
        timestamp = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp

    method = request.get('method', 'N/A')
    status = response.get('status', 'N/A')
    duration = response.get('duration', 0)
    duration_str = f"{duration}ms" if duration else "N/A"

    # Header
    print("\n" + "┌" + "─" * 48 + "┐")
    print(f"│ REQUEST #{request_number} │ {timestamp} │ {method} │ {duration_str}")
    print(f"│ {short_url}")
    print("└" + "─" * 48 + "┘")

    print(f"URL: {full_url}")
    print(f"Status: {status}")
    print("─" * 50)

def print_enhanced_request_response(req_resp, request_number, config):
    """Print a request/response pair with enhanced details."""
    request = req_resp.get('request', {})
    response = req_resp.get('response', {})

    # Extract short URL
    full_url = request.get('url', 'N/A')
    short_url = full_url.split('/')[-1] if '/' in full_url else full_url
    if len(short_url) > 30:
        short_url = short_url[:30] + '...'

    timestamp = request.get('timestamp', 'N/A')
    if timestamp != 'N/A':
        timestamp = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp

    method = request.get('method', 'N/A')

    # Duration
    duration = response.get('duration', 0)
    duration_str = f"{duration}ms" if duration else "N/A"

    # Header with request number, time, method, and URL
    print("\n" + "┌" + "─" * 48 + "┐")
    print(f"│ REQUEST #{request_number} │ {timestamp} │ {method} │ {duration_str}")
    print(f"│ {short_url}")
    print("└" + "─" * 48 + "┘")

    # REQUEST
    print(f"\n📤 REQUEST")
    print(f"URL: {full_url}")
    print(f"Method: {method}")

    # Request headers
    if config['capture_headers'] and request.get('headers'):
        print(f"\nHeaders:")
        for key, value in request['headers'].items():
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            print(f"  {key}: {value_str}")

    # Request body
    if request.get('body'):
        print(f"\nBody:")
        try:
            body_str = json.dumps(request['body'], indent=2)
            if len(body_str) > config['max_body_length']:
                print(body_str[:config['max_body_length']] + "\n... (truncated)")
            else:
                print(body_str)
        except:
            body_str = str(request['body'])
            if len(body_str) > config['max_body_length']:
                print(body_str[:config['max_body_length']] + "... (truncated)")
            else:
                print(body_str)

    # RESPONSE
    if response:
        # Check for errors
        if response.get('error'):
            print(f"\n❌ ERROR")
            print(f"Error: {response['error']}")
            print(f"Duration: {duration_str}")
        else:
            status = response.get('status', 'N/A')
            status_text = response.get('statusText', '')

            # Color code status
            if status >= 200 and status < 300:
                status_icon = "✅"
            elif status >= 300 and status < 400:
                status_icon = "🔄"
            elif status >= 400 and status < 500:
                status_icon = "⚠️"
            else:
                status_icon = "❌"

            print(f"\n📥 RESPONSE {status_icon}")
            print(f"Status: {status} {status_text}")
            print(f"Duration: {duration_str}")

            # Response headers
            if config['capture_headers'] and response.get('headers'):
                print(f"\nHeaders:")
                for key, value in response['headers'].items():
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"  {key}: {value_str}")

            # Response body
            if response.get('body'):
                print(f"\nBody:")
                try:
                    body = response['body']
                    body_str = json.dumps(body, indent=2)
                    if len(body_str) > config['max_body_length']:
                        print(body_str[:config['max_body_length']] + "\n... (truncated)")
                    else:
                        print(body_str)
                except:
                    body_str = str(response['body'])
                    if len(body_str) > config['max_body_length']:
                        print(body_str[:config['max_body_length']] + "... (truncated)")
                    else:
                        print(body_str)

    print("\n" + "─" * 50)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start streaming network monitor with command line arguments."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle special flags
    if args.list_presets:
        list_presets()
        sys.exit(0)

    # Build configuration
    config = build_config_from_args(args)

    print("\n🚀 Starting Network Stream Monitor...")
    print(f"Preset: {args.preset}")
    print(f"Profile: {args.profile}")

    driver = initialize_driver(args.profile)

    try:
        # Navigate to URL
        print(f"🌐 Navigating to {args.url}...")
        driver.get(args.url)
        time.sleep(3)

        # Install monitor
        install_enhanced_monitor(driver, config)
        print("✅ Monitor installed!\n")

        # Start streaming
        stream_network_activity(driver, config)

    except Exception as e:
        # Only show error if it's not a session/connection error
        if not isinstance(e, (WebDriverException, InvalidSessionIdException)):
            print(f"\n❌ Error: {e}")
    finally:
        # Try to quit driver, but don't fail if browser already closed
        try:
            if is_driver_alive(driver):
                driver.quit()
        except:
            pass
        print("👋 Exited cleanly")

if __name__ == "__main__":
    main()
