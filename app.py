import requests
import json
import time
import urllib.parse

# ==============================
# Akash Go → Playlist Generator
# ==============================

STATIC_AUTH_TOKEN = "zaEUQQBobbev0pzWcF9CJGuTWK5wtbBX"
SUBSCRIBER_ID = "41192391"
DATA_FILE = "data.json"
OUTPUT_M3U = "playlist.m3u"


def fetch_tokens(content_id):
    """Fetch fresh bearer and license session tokens."""
    token_url = "https://kong.akash-go.com/auth/auth-service/v1/oauth/token-service/token"
    token_payload = {
        "action": "stream",
        "epids": [],
        "provider": "AkashGo",
        "contentId": content_id
    }

    token_headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "appversion": "1.0.34",
        "authorization": f"bearer {STATIC_AUTH_TOKEN}",
        "baid": "1001063469",
        "dthstatus": "DTH With Binge",
        "origin": "https://www.akashgo.com",
        "platform": "binge_anywhere_web",
        "referer": "https://www.akashgo.com/",
        "subscriberid": SUBSCRIBER_ID,
        "subscriptiontype": "FREEMIUM",
        "x-app-id": "123456",
        "x-app-key": "123456",
        "x-authenticated-userid": SUBSCRIBER_ID,
        "x-device-id": str(int(time.time() * 1000)),
        "x-device-platform": "PC",
        "x-device-type": "ANDROID",
        "x-subscriber-id": SUBSCRIBER_ID,
        "x-subscriber-name": "CoderBoyBD",
        "user-agent": "okhttp/4.9.3"
    }

    try:
        response = requests.post(token_url, headers=token_headers, json=token_payload, timeout=10)
        data = response.json()
        if data.get("code") != 0:
            print(f"[] Token error for {content_id}: {data.get('message')}")
            return None, None
        return data["data"]["token"], data["data"]["param2"]
    except Exception as e:
        print(f"[] Token fetch failed for {content_id}: {e}")
        return None, None


def fetch_content(content_id, bearer_token, license_session):
    """Fetch content details for given ID."""
    url = f"https://kong.akash-go.com/content-subscriber-detail/api/content/info/vod/{content_id}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {bearer_token}",
        "user-agent": "okhttp/4.9.3"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data.get("code") != 0:
            print(f"[] Content error for {content_id}: {data.get('message')}")
            return None

        meta = data["data"]["meta"]
        detail = data["data"]["detail"]

        mpd = detail.get("dashWidewinePlayUrl")
        license_url = detail.get("dashWidewineLicenseUrl")
        poster = meta.get("posterImage")
        title = meta.get("vodTitle", f"Content_{content_id}")

        if not mpd or not license_url:
            print(f"[] Missing stream info for {content_id}")
            return None

        encoded_session = urllib.parse.quote(license_session, safe="")
        full_license = f"{license_url}&ls_session={encoded_session}"

        return {
            "title": title,
            "mpd": mpd,
            "license": full_license,
            "poster": poster
        }

    except Exception as e:
        print(f"[] Failed fetching content {content_id}: {e}")
        return None


def make_m3u_entry(info, category):
    """Create one M3U entry block with category support."""
    title = info["title"]
    mpd = info["mpd"]
    poster = info["poster"]
    license_url = info["license"]

    return f'''#EXTINF:-1 group-title="AkashGo | {category}" tvg-id="" tvg-logo="{poster}", {title}
#EXTVLCOPT:http-user-agent=Mozilla/5.0(coderboybd) (Linux; Android 9; Redmi S2 Build/PKQ1.181203.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.79 Mobile Safari/537.36
#KODIPROP:inputstream.adaptive.manifest_type=dash
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key={license_url}
{mpd}

'''


if __name__ == "__main__":
    print("=== Akash Go → Playlist Generator ===\n")

    # Load data.json
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[] Failed to read {DATA_FILE}: {e}")
        exit()

    m3u_output = "#EXTM3U\n\n"

    for category, items in data.items():
        print(f"\n=== Category: {category} ===")
        m3u_output += f"# ===== {category} =====\n"

        for content_id in items.keys():
            print(f"[] Processing Content ID: {content_id}")

            bearer, ls_token = fetch_tokens(content_id)
            if not bearer or not ls_token:
                continue

            content_info = fetch_content(content_id, bearer, ls_token)
            if content_info:
                entry = make_m3u_entry(content_info, category)
                m3u_output += entry
                print(f"[] Added: {content_info['title']}")
            else:
                print(f"[] Skipped Content ID {content_id}")

        m3u_output += "\n"

    # Save final playlist
    try:
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write(m3u_output)
        print(f"\n✅ Playlist generated successfully → {OUTPUT_M3U}")
    except Exception as e:
        print(f"[] Failed to save playlist: {e}")
