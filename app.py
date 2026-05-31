from radio import get_service

service = get_service()
service.apply_saved_volume()
service.play_current(announce=True)

while True:
    cmd = input(
        "\n[n]ext [p]rev [t]oggle [x]stop [+]vol [-]vol "
        "[s]tatus [f]av [v]iew favs [l]anguage [r]efresh [q]uit : "
    ).lower().strip()

    if cmd in ("n", "next"):
        service.next()
        print("Playing:", service.current_station()["name"])

    elif cmd in ("p", "prev"):
        service.previous()
        print("Playing:", service.current_station()["name"])

    elif cmd in ("t", "toggle"):
        service.toggle_playback()

    elif cmd in ("+", "volup"):
        vol = service.volume_up()
        print(f"Volume: {vol}")

    elif cmd in ("-", "voldown"):
        vol = service.volume_down()
        print(f"Volume: {vol}")

    elif cmd in ("s", "status"):
        service.print_status()

    elif cmd in ("f", "favorite"):
        station = service.add_current_favorite()
        print()
        print("Added to favorites:")
        print(station["name"])

    elif cmd in ("v", "favorites"):
        print()
        for station in service.list_favorites():
            print(station["name"])

    elif cmd in ("x", "stop"):
        service.stop_playback()

    elif cmd in ("r", "refresh"):
        service.refresh_stations(force=True)
        service._resolve_current_index()
        service.play_current(announce=True)

    elif cmd in ("l", "language", "lang"):
        print(f"Current language: {service.config['language']}")
        print("Examples:", ", ".join(service.available_languages()))
        lang = input("New language: ").strip().lower()
        if lang:
            service.set_language(lang)
            print("Language:", lang)
            print("Playing:", service.current_station()["name"])

    elif cmd in ("q", "quit"):
        break
