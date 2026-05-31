const els = {
  stationName: document.getElementById("station-name"),
  streamMeta: document.getElementById("stream-meta"),
  stateBadge: document.getElementById("state-badge"),
  volume: document.getElementById("volume"),
  country: document.getElementById("country"),
  codec: document.getElementById("codec"),
  stationIndex: document.getElementById("station-index"),
  favoritesList: document.getElementById("favorites-list"),
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { Accept: "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`);
  }
  return res.json();
}

function setBadge(state) {
  els.stateBadge.textContent = state;
  els.stateBadge.className = "badge";
  if (state === "play") {
    els.stateBadge.classList.add("badge--play");
  } else if (state === "pause") {
    els.stateBadge.classList.add("badge--pause");
  } else {
    els.stateBadge.classList.add("badge--stop");
  }
}

function renderStatus(data) {
  const station = data.station || {};
  const stream = data.stream || {};

  els.stationName.textContent = station.name || "—";
  const meta = [stream.artist, stream.title].filter(Boolean).join(" — ");
  els.streamMeta.textContent = meta || station.tags || "";
  setBadge(data.state || "stop");

  const vol = data.mpc_volume ?? data.volume;
  els.volume.textContent = vol != null ? `${vol}%` : "—";
  els.country.textContent = station.country || "—";
  els.codec.textContent = station.codec
    ? `${station.codec}${station.bitrate ? ` @ ${station.bitrate}k` : ""}`
    : "—";
  els.stationIndex.textContent =
    data.station_count != null
      ? `${(data.index ?? 0) + 1} / ${data.station_count}`
      : "—";
}

function renderFavorites(favorites) {
  els.favoritesList.innerHTML = "";
  if (!favorites.length) {
    const li = document.createElement("li");
    li.textContent = "No favorites yet";
    li.style.color = "var(--muted)";
    els.favoritesList.appendChild(li);
    return;
  }

  for (const fav of favorites) {
    const li = document.createElement("li");

    const playBtn = document.createElement("button");
    playBtn.className = "fav-play";
    playBtn.textContent = "▶";
    playBtn.title = "Play";
    playBtn.addEventListener("click", async () => {
      await api("/api/favorites/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: fav.url }),
      });
      await refresh();
    });

    const name = document.createElement("span");
    name.className = "fav-name";
    name.textContent = fav.name;
    name.title = fav.name;

    const removeBtn = document.createElement("button");
    removeBtn.className = "fav-remove";
    removeBtn.textContent = "×";
    removeBtn.title = "Remove";
    removeBtn.addEventListener("click", async () => {
      await api(`/api/favorites?url=${encodeURIComponent(fav.url)}`, {
        method: "DELETE",
      });
      await refresh();
    });

    li.append(playBtn, name, removeBtn);
    els.favoritesList.appendChild(li);
  }
}

async function loadLanguages(current) {
  const data = await api("/api/languages");
  const select = document.getElementById("language-select");
  select.innerHTML = "";
  const langs = data.languages || [];
  const cur = current || data.current;
  if (cur && !langs.includes(cur)) {
    langs.unshift(cur);
  }
  for (const lang of langs) {
    const opt = document.createElement("option");
    opt.value = lang;
    opt.textContent = lang;
    if (lang === cur) {
      opt.selected = true;
    }
    select.appendChild(opt);
  }
}

async function refresh() {
  const [status, favs] = await Promise.all([
    api("/api/status"),
    api("/api/favorites"),
  ]);
  renderStatus(status);
  renderFavorites(favs.favorites || []);
  await loadLanguages(status.language);
}

document.getElementById("btn-prev").addEventListener("click", async () => {
  await api("/api/prev", { method: "POST" });
  await refresh();
});

document.getElementById("btn-next").addEventListener("click", async () => {
  await api("/api/next", { method: "POST" });
  await refresh();
});

document.getElementById("btn-toggle").addEventListener("click", async () => {
  await api("/api/toggle", { method: "POST" });
  await refresh();
});

document.getElementById("btn-vol-up").addEventListener("click", async () => {
  await api("/api/volume/up", { method: "POST" });
  await refresh();
});

document.getElementById("btn-vol-down").addEventListener("click", async () => {
  await api("/api/volume/down", { method: "POST" });
  await refresh();
});

document.getElementById("btn-fav-add").addEventListener("click", async () => {
  await api("/api/favorites", { method: "POST" });
  await refresh();
});

document.getElementById("btn-language").addEventListener("click", async () => {
  const language = document.getElementById("language-select").value;
  await api("/api/language", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language }),
  });
  await refresh();
});

refresh();
setInterval(refresh, 5000);
