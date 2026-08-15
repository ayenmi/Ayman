#!/usr/bin/env python3
import sys
import os
import json
import hashlib
from time import sleep
import argparse
import requests
from bs4 import BeautifulSoup

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except Exception:
    # Fallback if colorama is not available
    class _NoColor:
        def __getattr__(self, _):
            return ""
    Fore = Style = _NoColor()


class SnapchatDownloader:
    def __init__(self, timeout=12, no_color=False):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.base_url = "https://story.snapchat.com/@"
        self.timeout = timeout
        if no_color:
            # disable color output
            class _NoColor:
                def __getattr__(self, _):
                    return ""
            global Fore, Style
            Fore = Style = _NoColor()

    def banner(self):
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception:
            pass
        print(Fore.CYAN + Style.BRIGHT + """
  ██╗   ██╗     ██████╗     ███████╗
  ╚██╗ ██╔╝    ██╔════╝     ██╔════╝
   ╚████╔╝     ██║          █████╗  
    ╚██╔╝      ██║          ██╔══╝  
     ██║   ██╗ ╚██████╗ ██╗ ██║     
     ╚═╝   ╚═╝  ╚═════╝ ╚═╝ ╚═╝     
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [★] Snapchat Story Saver v2.0
  [★] Dev     : Y.C.F Team
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    def fetch_profile_data(self, username):
        url = f"{self.base_url}{username}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 404:
                print(Fore.RED + f"[-] Error: User '@{username}' not found.")
                return None
            response.raise_for_status()
        except requests.RequestException as e:
            print(Fore.RED + f"[-] Network Error: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")

        target_script = None
        for script in scripts:
            if script.string and ("__NEXT_DATA__" in script.string or "props" in script.string):
                target_script = script.string
                break

        if not target_script:
            print(Fore.RED + "[-] Failed to parse Snapchat layout structure.")
            return None

        try:
            return json.loads(target_script.strip())
        except json.JSONDecodeError:
            print(Fore.RED + "[-] Error decoding JSON payload.")
            return None

    def extract_info(self, data):
        try:
            page_props = data.get("props", {}).get("pageProps", {})
            user_profile = page_props.get("userProfile", {})

            info = user_profile.get("publicProfileInfo") or user_profile.get("userInfo") or {}
            bio = info.get("bio") or info.get("displayName") or "No Bio Available"
            snapcode = info.get("snapcodeImageUrl", "N/A")
            snaps = page_props.get("story", {}).get("snapList", [])

            return {
                "bio": bio,
                "snapcode": snapcode,
                "snaps": snaps
            }
        except Exception:
            return None

    def download_snaps(self, username, snaps, output_dir=None):
        if not snaps:
            print(Fore.YELLOW + f"[!] No active stories found for @{username}.")
            return

        save_dir = output_dir or f"snaps_{username}"
        os.makedirs(save_dir, exist_ok=True)

        print(Fore.GREEN + f"[+] Found {len(snaps)} story media item(s). Saving to './{save_dir}'...\n")

        for idx, snap in enumerate(snaps, 1):
            media_url = snap.get("snapUrls", {}).get("mediaUrl") or snap.get("snapMediaUrl")
            if not media_url:
                continue

            try:
                res = self.session.get(media_url, stream=True, timeout=self.timeout)
                if res.status_code != 200:
                    print(Fore.RED + f"[-] [{idx}/{len(snaps)}] Failed to load stream.")
                    continue

                content_type = res.headers.get("Content-Type", "")
                ext = ".mp4" if "video" in content_type else ".jpeg"

                snap_id = None
                if isinstance(snap.get("snapId"), dict):
                    snap_id = snap.get("snapId", {}).get("value")
                if not snap_id:
                    snap_id = snap.get("id")
                if not snap_id:
                    snap_id = hashlib.md5(media_url.encode()).hexdigest()[:10]

                filename = os.path.join(save_dir, f"{username}_{snap_id}{ext}")

                if os.path.exists(filename):
                    print(Fore.YELLOW + f"[*] [{idx}/{len(snaps)}] Skipped (Already exists): {snap_id}{ext}")
                    continue

                with open(filename, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                print(Fore.GREEN + f"[✓] [{idx}/{len(snaps)}] Downloaded: {snap_id}{ext}")
                sleep(0.2)

            except requests.RequestException as err:
                print(Fore.RED + f"[-] [{idx}/{len(snaps)}] Connection dropped: {err}")

    def run(self, username=None, output_dir=None):
        self.banner()
        try:
            target = username
            if not target:
                # interactive fallback
                target = input(Fore.WHITE + Style.BRIGHT + "[?] Enter Target Username: ").strip().lstrip('@')

            if not target:
                print(Fore.RED + "[-] Username cannot be empty.")
                return

            print(Fore.BLUE + f"\n[*] Fetching target profile @{target}...")
            raw_data = self.fetch_profile_data(target)
            if not raw_data:
                return

            info = self.extract_info(raw_data)
            if not info:
                print(Fore.RED + "[-] Profile extraction failed.")
                return

            print(Fore.MAGENTA + f"[•] Bio      : {info['bio']}")
            print(Fore.MAGENTA + f"[•] Snapcode : {info['snapcode']}\n")

            self.download_snaps(target, info['snaps'], output_dir=output_dir)
            print(Fore.GREEN + Style.BRIGHT + "\n[+] Operation completed successfully.")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n[!] Aborted by user.")
            sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description='Snapchat story downloader (cli)')
    parser.add_argument('-u', '--user', help='Target Snapchat username (without @)')
    parser.add_argument('-o', '--output-dir', help='Directory to save snaps into', default=None)
    parser.add_argument('-t', '--timeout', help='Network timeout in seconds', type=int, default=12)
    parser.add_argument('--no-color', help='Disable colored output', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    downloader = SnapchatDownloader(timeout=args.timeout, no_color=args.no_color)
    downloader.run(username=args.user, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
