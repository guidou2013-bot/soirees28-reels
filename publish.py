#!/usr/bin/env python3
"""Publieur des Reels promo @soireeschartres28 (28/09/2026). Copie du robot PSK, adaptee.
- Facebook : programmation NATIVE Meta (scheduled_publish_time) des qu'on entre dans la fenetre de 29 jours.
- Instagram : publication a l'heure dite (l'API IG ne sait pas programmer).
- Stories autonomes (type "story") : Instagram + Facebook a l'heure dite.
Token = secret META_PAGE_TOKEN (utilisateur systeme ou token de Page) -> Page resolue via me/accounts.
Medias heberges par GitHub Pages sur ce depot (dossier media/).
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

GRAPH = "https://graph.facebook.com/v23.0"
SYS_TOKEN = os.environ.get("META_PAGE_TOKEN", "").strip()
PAGE_TOKEN = None
DRY = os.environ.get("DRY_RUN", "") == "1"
GRACE_HOURS = 12
FB_MIN_LEAD = timedelta(minutes=15)
FB_MAX_LEAD = timedelta(days=28)  # Meta refuse au-dela de 29 jours : on garde une marge
PAGE_NAME_HINT = "soireeschartres28"
BILAN = []  # lignes envoyees sur Telegram en fin de run


def api(method, path, token=None, **params):
    params["access_token"] = token or PAGE_TOKEN or SYS_TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    req = urllib.request.Request(f"{url}?{data.decode()}") if method == "GET" \
        else urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:300]}")


def resolve():
    global PAGE_TOKEN
    pages = api("GET", "me/accounts", token=SYS_TOKEN,
                fields="id,name,access_token,instagram_business_account")
    data = pages.get("data", [])
    if not data:
        # Token de Page directement (pas d'utilisateur systeme) : me = la Page
        me = api("GET", "me", token=SYS_TOKEN, fields="id,name,instagram_business_account")
        PAGE_TOKEN = SYS_TOKEN
        return me, (me.get("instagram_business_account") or {}).get("id")
    page = next((p for p in data if PAGE_NAME_HINT in p.get("name", "").lower()), None)
    if not page:
        noms = ", ".join(p.get("name", "?") for p in data)
        raise RuntimeError(f"Page SoireesChartres28 introuvable parmi : {noms}")
    PAGE_TOKEN = page.get("access_token") or SYS_TOKEN
    return page, (page.get("instagram_business_account") or {}).get("id")


def attendre(cid, essais, pause=5):
    for _ in range(essais):
        sc = api("GET", cid, fields="status_code").get("status_code")
        if sc == "FINISHED":
            return
        if sc == "ERROR":
            raise RuntimeError("conteneur IG en erreur")
        time.sleep(pause)
    raise RuntimeError("conteneur IG : delai de traitement depasse")


def legende(p, reseau):
    # Facebook : pas de @ (les profils perso ne se taguent pas depuis une Page)
    if reseau == "fb":
        return p.get("caption_fb") or p.get("caption", "")
    return p.get("caption", "")


def ig_publier(ig_id, p, est_video):
    if p.get("type") == "story":
        champ = {"video_url": p["video"]} if est_video else {"image_url": p["image"]}
        c = api("POST", f"{ig_id}/media", media_type="STORIES", **champ)
    elif est_video:
        c = api("POST", f"{ig_id}/media", media_type="REELS", video_url=p["video"],
                caption=legende(p, "ig"), share_to_feed="true")
    elif p.get("type") == "carousel" and p.get("images"):
        enfants = []
        for url in p["images"][:10]:
            e = api("POST", f"{ig_id}/media", image_url=url, is_carousel_item="true")
            attendre(e["id"], 20, 3)
            enfants.append(e["id"])
        c = api("POST", f"{ig_id}/media", media_type="CAROUSEL", caption=legende(p, "ig"),
                children=",".join(enfants))
    else:
        c = api("POST", f"{ig_id}/media", image_url=p["image"], caption=legende(p, "ig"))
    attendre(c["id"], 60 if est_video else 20)
    return api("POST", f"{ig_id}/media_publish", creation_id=c["id"]).get("id")


def fb_story(page_id, p, est_video):
    if est_video:
        # Story video Facebook : demarrer, envoyer par URL, terminer
        d = api("POST", f"{page_id}/video_stories", upload_phase="start")
        vid = d["video_id"]
        req = urllib.request.Request(d["upload_url"], method="POST",
                                     headers={"Authorization": f"OAuth {PAGE_TOKEN}", "file_url": p["video"]})
        urllib.request.urlopen(req, timeout=120).read()
        r = api("POST", f"{page_id}/video_stories", upload_phase="finish", video_id=vid)
        return r.get("post_id") or vid
    ph = api("POST", f"{page_id}/photos", url=p["image"], published="false")
    r = api("POST", f"{page_id}/photo_stories", photo_id=ph["id"])
    return r.get("post_id") or ph["id"]


def main():
    if not SYS_TOKEN:
        print("META_PAGE_TOKEN absent : rien a faire tant que le jeton n'est pas pose.")
        return
    page, ig_id = resolve()
    print(f"Page: {page['name']} ({page['id']}) | Instagram lie: {ig_id or 'NON LIE'}")
    if os.environ.get("CHECK_ONLY") == "1":
        sp = api("GET", f"{page['id']}/scheduled_posts", fields="id,scheduled_publish_time")
        print(f"Posts deja programmes sur la Page (Business Suite compris) : {len(sp.get('data', []))}")
        if ig_id:
            ig = api("GET", ig_id, fields="username,followers_count")
            print(f"Instagram : @{ig.get('username')} ({ig.get('followers_count')} abonnes)")
        BILAN.append(f"Test de connexion OK : {page['name']} + Instagram {'lie' if ig_id else 'NON LIE'}")
        return

    sched = json.load(open("schedule.json", encoding="utf-8"))
    tz = ZoneInfo(sched.get("timezone", "Europe/Paris"))
    now = datetime.now(tz)
    changed = 0

    for p in sched["posts"]:
        quand = datetime.fromisoformat(p["quand"]).replace(tzinfo=tz)
        st = p.get("statut", "planifie")
        if st not in ("planifie", "partiel"):
            continue
        lead = quand - now
        est_video = bool(p.get("video"))
        story = p.get("type") == "story"
        titre = p.get("titre", p["id"])
        dans_fenetre = timedelta(0) <= (now - quand) <= timedelta(hours=GRACE_HOURS)

        # FACEBOOK (feed) : programmation native, une seule fois
        if not story and not p.get("fb_done"):
            if FB_MIN_LEAD <= lead <= FB_MAX_LEAD or timedelta(0) < lead < FB_MIN_LEAD or dans_fenetre:
                programme = lead >= FB_MIN_LEAD
                if DRY:
                    print(f"[dry] FB {'programmerait' if programme else 'publierait'} {p['id']} @ {p['quand']}")
                else:
                    try:
                        extra = {"published": "false", "scheduled_publish_time": str(int(quand.timestamp()))} if programme else {}
                        if est_video:
                            r = api("POST", f"{page['id']}/videos", file_url=p["video"],
                                    description=legende(p, "fb"), **extra)
                        else:
                            r = api("POST", f"{page['id']}/photos", url=p["image"],
                                    caption=legende(p, "fb"), **extra)
                        p["fb_post_id"] = r.get("post_id") or r.get("id"); p["fb_done"] = True
                        p.pop("fb_error", None)
                        print(f"FB ok {p['id']}"); changed += 1
                        BILAN.append(f"Facebook {'programme' if programme else 'publie'} : {titre} ({quand:%d/%m %H:%M})")
                    except Exception as e:
                        p["fb_error"] = str(e)[:300]; print(f"FB ERREUR {p['id']}: {p['fb_error']}")
                        BILAN.append(f"ERREUR Facebook : {titre} : {p['fb_error'][:150]}")

        # FACEBOOK (story) : a l'heure dite
        if story and not p.get("fb_done") and dans_fenetre and not DRY:
            try:
                p["fb_post_id"] = fb_story(page["id"], p, est_video); p["fb_done"] = True
                print(f"FB story ok {p['id']}"); changed += 1
                BILAN.append(f"Story Facebook publiee : {titre}")
            except Exception as e:
                p["fb_error"] = str(e)[:300]; print(f"FB STORY ERREUR {p['id']}: {p['fb_error']}")
                BILAN.append(f"ERREUR story Facebook : {titre} : {p['fb_error'][:150]}")

        # INSTAGRAM : a l'heure dite
        if not p.get("ig_done") and ig_id and dans_fenetre:
            if DRY:
                print(f"[dry] IG publierait {p['id']}")
            else:
                try:
                    p["ig_media_id"] = ig_publier(ig_id, p, est_video); p["ig_done"] = True
                    p.pop("ig_error", None)
                    print(f"IG ok {p['id']}"); changed += 1
                    BILAN.append(f"Instagram publie : {titre}")
                except Exception as e:
                    p["ig_error"] = str(e)[:300]; print(f"IG ERREUR {p['id']}: {p['ig_error']}")
                    BILAN.append(f"ERREUR Instagram : {titre} : {p['ig_error'][:150]}")

        if p.get("fb_done") and (p.get("ig_done") or not ig_id):
            p["statut"] = "publie"
        elif p.get("fb_done") or p.get("ig_done"):
            p["statut"] = "partiel"
        if (now - quand) > timedelta(hours=GRACE_HOURS) and p["statut"] != "publie":
            p["statut"] = "manque"
            BILAN.append(f"MANQUE (plus de {GRACE_HOURS} h de retard, a replanifier) : {titre}")

    json.dump(sched, open("schedule.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{now:%d/%m %H:%M} | {changed} action(s).")


if __name__ == "__main__":
    try:
        main()
    finally:
        with open("bilan.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(BILAN))
