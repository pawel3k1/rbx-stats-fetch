import os
import json
import requests
import shutil
from datetime import date, datetime

def fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses=False):
    # Lists to track saved files and errors for the summary report
    saved_files = []
    error_files = []
    for endpoint in endpoints:
        endpoint = endpoint.lstrip('/')
        # Construct the URL with the API key
        if '?' in endpoint:
            url = base_url + endpoint + "&api=" + api_key
        else:
            url = base_url + endpoint + "?api=" + api_key

        # Make the HTTP request
        response = requests.get(url, headers=headers)
        try:
            # Check for success only for options without all_responses
            if not all_responses and response.status_code != 200:
                raise requests.exceptions.RequestException(f"Status code: {response.status_code}")

            # Parse the response
            if endpoint.endswith("/plain"):
                # For /plain endpoints, save as text
                data = response.text
                filename = endpoint.replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_') + ".txt"
                filepath = os.path.join(folder_name, filename)
                with open(filepath, 'w') as f:
                    f.write(data)
                print(f"Saved {filename}")
                saved_files.append(filename)
            else:
                # For other endpoints, save as JSON
                try:
                    data = response.json()
                except ValueError:
                    data = {"error": "Invalid JSON format", "response_text": response.text}
                filename = endpoint.replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_') + ".json"
                filepath = os.path.join(folder_name, filename)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"Saved {filename}")
                saved_files.append(filename)
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching {endpoint}: {str(e)} (Status code: {response.status_code})"
            print(error_message)
            # Save the error, always for options with all_responses
            if all_responses or response.status_code != 200:
                error_filename = f"error_{endpoint.replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_')}.log"
                error_filepath = os.path.join(folder_name, error_filename)
                with open(error_filepath, 'w') as f:
                    f.write(error_message + "\n")
                    try:
                        error_details = response.json()
                        f.write(f"Error details: {json.dumps(error_details, indent=4)}\n")
                    except ValueError:
                        f.write(f"Error details: {response.text}\n")
                error_files.append((error_filename, f"Status code: {response.status_code}"))
    return saved_files, error_files

def generate_summary(folder_name, saved_files, error_files):
    # Generate a summary report of saved files and errors
    summary_file = os.path.join(folder_name, "summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Data Saving Report ({folder_name}):\n")
        f.write("Saved Files:\n")
        for file in saved_files:
            f.write(f"- {file}\n")
        f.write("Errors:\n")
        if error_files:
            for file, status in error_files:
                f.write(f"- {file}: {status}\n")
        else:
            f.write("- No errors\n")
    print(f"Generated summary report: {summary_file}")

def test_request(base_url, api_key):
    # Perform a test request with custom parameters and headers
    endpoint = input("Enter endpoint (e.g., offsets): ").strip().lstrip('/')
    params_input = input("Enter additional parameters (e.g., version=latest, press enter to skip): ").strip()
    params = {}
    if params_input:
        for param in params_input.split():
            if '=' in param:
                key, value = param.split('=')
                params[key] = value
    params['api'] = api_key

    headers = {
        "Accept": "application/json",
    }
    custom_ua = input("Add a custom User-Agent? (yes/no): ").strip().lower()
    if custom_ua == "yes":
        headers["User-Agent"] = input("Enter User-Agent: ").strip()
    else:
        headers["User-Agent"] = "rbxstats-api-fetcher/1.0 (Python/3.x)"

    url = base_url + endpoint
    response = requests.get(url, headers=headers, params=params)
    print(f"\nResult of test request to {url}:")
    print(f"Status code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=4)}")
    except ValueError:
        print(f"Response: {response.text}")

def main():
    # Fixed API key
    api_key = ""
    # Full list of default endpoints (from documentation)
    all_endpoints = [
        "offsets", "offsets/plain", "offsets/shuffles", "offsets/shuffles/plain",
        "offsets/shuffles/search/test", "offsets/shuffles/search/test/plain",
        "offsets/search/test", "offsets/search/test/plain",
        "offsets/prefix/test", "offsets/prefix/test/plain",
        "offsets/camera", "offsets/camera/plain",
        "offsets/game/123", "offsets/game/123/plain",
        "exploits", "exploits/windows", "exploits/mac",
        "exploits/detected", "exploits/undetected",
        "exploits/free", "exploits/paid", "exploits/indev",
        "exploits/summary", "exploits/count",
        "versions/latest", "versions/latest/plain",
        "versions/future", "versions/future/plain"
    ]
    # Filters for selective options
    offsets_endpoints = [
        ep for ep in all_endpoints
        if ep.startswith("offsets") and "shuffles" not in ep
    ]
    shuffles_endpoints = [
        ep for ep in all_endpoints
        if "shuffles" in ep
    ]
    versions_endpoints = [
        ep for ep in all_endpoints
        if ep.startswith("versions")
    ]
    # Endpoints with parameters
    param_endpoints_template = [
        "offsets/search/{name}", "offsets/search/{name}/plain",
        "offsets/prefix/{prefix}", "offsets/prefix/{prefix}/plain",
        "offsets/game/{game_id}", "offsets/game/{game_id}/plain",
        "offsets/shuffles/search/{name}", "offsets/shuffles/search/{name}/plain"
    ]
    base_url = "https://api.rbxstats.xyz/api/"
    today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # e.g., 2025-05-15_19-58-00
    folder_name = today

    # HTTP headers
    headers = {
        "Accept": "application/json",
        "User-Agent": "rbxstats-api-fetcher/1.0 (Python/3.x)"
    }

    # Create folder with current date and time
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Interactive menu
    print("rbxstats API Data Fetching CLI Tool")
    print("1. Fetch all default endpoints")
    print("2. Enter endpoints manually")
    print("3. Save all responses (regardless of response code)")
    print("4. Save only Offsets (excluding Shuffles, regardless of response code)")
    print("5. Save only Shuffles (regardless of response code)")
    print("6. Save only Versions (regardless of response code)")
    print("7. Save endpoints with parameters (e.g., search/test, prefix/test, game/123)")
    print("8. Generate a summary report after saving data")
    print("9. Clean the data folder before saving")
    print("10. Perform a test request to a single endpoint (with custom headers and parameters)")
    choice = input("Select an option (1-10): ").strip()

    # Select endpoints based on the option
    saved_files = []
    error_files = []
    if choice == "1":
        endpoints = all_endpoints
        all_responses = False
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "2":
        endpoints_input = input("Enter endpoints (space-separated, e.g., offsets search?query=test): ").strip()
        endpoints = endpoints_input.split() if endpoints_input else []
        all_responses = False
        if endpoints:
            saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "3":
        endpoints = all_endpoints
        all_responses = True
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "4":
        endpoints = offsets_endpoints
        all_responses = True
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "5":
        endpoints = shuffles_endpoints
        all_responses = True
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "6":
        endpoints = versions_endpoints
        all_responses = True
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "7":
        # Input values for endpoints with parameters
        search_name = input("Enter value for search (e.g., test): ").strip() or "test"
        prefix_value = input("Enter value for prefix (e.g., test): ").strip() or "test"
        game_id = input("Enter game ID (e.g., 123): ").strip() or "123"
        endpoints = [
            ep.format(name=search_name, prefix=prefix_value, game_id=game_id)
            for ep in param_endpoints_template
        ]
        all_responses = True
        saved_files, error_files = fetch_and_save(endpoints, folder_name, api_key, headers, base_url, all_responses)
    elif choice == "8":
        # Generate summary report
        if not saved_files and not error_files:
            print("Run another option (1-7) first to save data!")
        else:
            generate_summary(folder_name, saved_files, error_files)
    elif choice == "9":
        # Clean the folder
        confirm = input(f"Are you sure you want to clean the folder {folder_name}? (yes/no): ").strip().lower()
        if confirm == "yes":
            if os.path.exists(folder_name):
                shutil.rmtree(folder_name)
                print(f"Cleared folder {folder_name}")
                os.makedirs(folder_name)
            else:
                print(f"Folder {folder_name} does not exist, created a new one")
                os.makedirs(folder_name)
        else:
            print("Folder cleaning canceled")
    elif choice == "10":
        # Test request
        test_request(base_url, api_key)
    else:
        print("Invalid option. Select 1-10.")
        return

    if choice in ["1", "2", "3", "4", "5", "6", "7"] and (saved_files or error_files):
        print("\nWould you like to generate a summary report? (yes/no): ")
        if input().strip().lower() == "yes":
            generate_summary(folder_name, saved_files, error_files)

if __name__ == "__main__":
    main()