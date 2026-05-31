const els = {
  stationName: document.getElementById("station-name"),
  streamMeta: document.getElementById("stream-meta"),
  stateBadge: document.getElementById("state-badge"),
  stationLogo: document.getElementById("station-logo"),
  volume: document.getElementById("volume"),
  browseMode: document.getElementById("browse-mode"),
  stationIndex: document.getElementById("station-index"),
  favoritesList: document.getElementById("favorites-list"),
  languageSelect: document.getElementById("language-select"),
  languageStatus: document.getElementById("language-status"),
  sleepStatus: document.getElementById("sleep-status"),
  sleepMinutes: document.getElementById("sleep-minutes"),
  tabAll: document.getElementById("tab-all"),
  tabFavorites: document.getElementById("tab-favorites"),
};

let activeLanguage = null;
let activeBrowseMode = "all";
let languageBusy = false;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { Accept: "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `${path} failed: ${res.status}`);
  }
  return res.json();
}

function setBadge(state) {
  els.stateBadge.textContent = state;
  els.stateBadge.className = "badge";
  if (state === "play") els.stateBadge.classList.add("badge--play");
  else if (state === "pause") els.stateBadge.classList.add("badge--pause");
  else els.stateBadge.classList.add("badge--stop");
}

function setBrowseTabs(mode) {
  activeBrowseMode = mode;
  els.tabAll.classList.toggle("tab--active", mode === "all");
  els.tabFavorites.classList.toggle("tab--active", mode === "favorites");
}

function renderLogo(station) {
  const url = station && station.favicon;
  if (url) {
    els.stationLogo.src = url;
    els.stationLogo.hidden = false;
    els.stationLogo.onerror = () => {
      els.stationLogo.hidden = true;
    };
  } else {
    els.stationLogo.hidden = true;
    els.stationLogo.removeAttribute("src");
  }
}

function renderSleep(sleep) {
  if (!sleep || !sleep.active) {
    els.sleepStatus.textContent = "Sleep timer off";
    return;
  }
  const min = Math.ceil(sleep.remaining_seconds / 60);
  els.sleepStatus.textContent = `Stops in ~${min} min`;
}

function renderStatus(data) {
  const station = data.station || {};
  const stream = data.stream || {};

  els.stationName.textContent = station.name || "—";
  const meta = [stream.artist, stream.title].filter(Boolean).join(" — ");
  els.streamMeta.textContent = meta || station.country || "";
  setBadge(data.state || "stop");
  renderLogo(station);

  const vol = data.mpc_volume ?? data.volume;
  els.volume.textContent = vol != null ? `${vol}%` : "—";
  els.browseMode.textContent = data.browse_mode || "all";
  els.stationIndex.textContent =
    data.station_count != null
      ? `${(data.index ?? 0) + 1} / ${data.station_count}`
      : "—";

  if (data.browse_mode) setBrowseTabs(data.browse_mode);
  if (data.sleep) renderSleep(data.sleep);

  if (data.language) {
    activeLanguage = data.language;
    syncLanguageSelect(data.language);
    if (!languageBusy) {
      els.languageStatus.textContent = `Active: ${data.language}`;
      els.languageStatus.classList.remove("language__status--busy");
    }
  }
}

function syncLanguageSelect(language) {
  if (languageBusy || document.activeElement === els.languageSelect) return;
  if ([...els.languageSelect.options].some((o) => o.value === language)) {
    els.languageSelect.value = language;
  }
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
    const removeBtn = document.createElement("button");
    removeBtn.className = "fav-remove";
    removeBtn.textContent = "×";
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

async function initLanguages() {
  const data = await api("/api/languages");
  els.languageSelect.innerHTML = "";
  const langs = [...(data.languages || [])];
  const cur = data.current || activeLanguage;
  if (cur && !langs.includes(cur)) langs.unshift(cur);
  for (const lang of langs) {
    const opt = document.createElement("option");
    opt.value = lang;
    opt.textContent = lang;
    els.languageSelect.appendChild(opt);
  }
  if (cur) {
    els.languageSelect.value = cur;
    activeLanguage = cur;
  }
}

async function applyLanguage(language) {
  if (!language || language === activeLanguage) return;
  languageBusy = true;
  els.languageSelect.disabled = true;
  els.languageStatus.textContent = `Switching to ${language}…`;
  els.languageStatus.classList.add("language__status--busy");
  try {
    const status = await api("/api/language", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language }),
    });
    activeLanguage = status.language;
    renderStatus(status);
    const favs = await api("/api/favorites");
    renderFavorites(favs.favorites || []);
  } catch (err) {
    els.languageStatus.textContent = err.message;
    syncLanguageSelect(activeLanguage);
  } finally {
    languageBusy = false;
    els.languageSelect.disabled = false;
    els.languageStatus.classList.remove("language__status--busy");
  }
}

async function setBrowseMode(mode) {
  await api("/api/browse-mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  await refresh();
}

async function refresh() {
  const [status, favs] = await Promise.all([
    api("/api/status"),
    api("/api/favorites"),
  ]);
  renderStatus(status);
  renderFavorites(favs.favorites || []);
}

els.languageSelect.addEventListener("change", () => {
  applyLanguage(els.languageSelect.value);
});

els.tabAll.addEventListener("click", () => setBrowseMode("all"));
els.tabFavorites.addEventListener("click", () => setBrowseMode("favorites"));

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

document.getElementById("btn-sleep-set").addEventListener("click", async () => {
  const minutes = parseInt(els.sleepMinutes.value, 10) || 0;
  await api("/api/sleep-timer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ minutes }),
  });
  await refresh();
});

document.getElementById("btn-sleep-clear").addEventListener("click", async () => {
  await api("/api/sleep-timer", { method: "DELETE" });
  els.sleepMinutes.value = "0";
  await refresh();
});

initLanguages().then(refresh);
setInterval(refresh, 8000);
