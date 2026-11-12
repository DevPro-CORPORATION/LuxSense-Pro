/**
 * LuxSense Pro — Official Website JavaScript
 * Handles dynamic GitHub Releases API synchronization, fallback manifests,
 * interactive telemetry previews, FAQ toggles, and clipboard actions.
 */

const GITHUB_OWNER = "DevPro-CORPORATION";
const GITHUB_REPO = "luxsense-pro";
const RELEASES_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases`;
const FALLBACK_MANIFEST_URL = "releases.json";

document.addEventListener("DOMContentLoaded", () => {
  initReleaseSync();
  initFaqAccordion();
  initLiveGaugeSimulation();
  initMobileNav();
  initCopyButtons();
});

/**
 * Synchronizes release information dynamically with GitHub Releases API,
 * with seamless fallback to embedded releases.json.
 */
async function initReleaseSync() {
  const versionTags = document.querySelectorAll(".dynamic-version");
  const dateElements = document.querySelectorAll(".dynamic-date");
  const installerLinks = document.querySelectorAll(".dynamic-installer-link");
  const portableLinks = document.querySelectorAll(".dynamic-portable-link");
  const shaInstaller = document.getElementById("sha-installer-val");
  const changelogBody = document.getElementById("dynamic-changelog");
  const prevReleasesContainer = document.getElementById("previous-releases-list");

  let releaseData = null;

  // 1. Attempt to fetch latest release from GitHub Public REST API
  try {
    const res = await fetch(`${RELEASES_API_URL}/latest`, {
      headers: { "Accept": "application/vnd.github.v3+json" }
    });
    if (res.ok) {
      const data = await res.json();
      releaseData = parseGitHubRelease(data);
    }
  } catch (err) {
    console.warn("GitHub API fetch error, switching to fallback manifest:", err);
  }

  // 2. Fallback to local releases.json if API is unavailable or rate-limited
  if (!releaseData) {
    try {
      const fallbackRes = await fetch(FALLBACK_MANIFEST_URL);
      if (fallbackRes.ok) {
        releaseData = await fallbackRes.json();
      }
    } catch (err) {
      console.warn("Fallback manifest read failed:", err);
    }
  }

  // Default hardcoded state if completely offline without JSON server
  if (!releaseData) {
    releaseData = {
      version: "2.1.0",
      tag_name: "v2.1.0",
      published_at: "2026-11-12",
      assets: {
        installer: {
          filename: "LuxSense-Pro-Setup-v2.1.0.exe",
          sha256: "a0a80e4060d152cb33cd9233f6072e9af1450774f8418c0565ccc65f05c3b478",
          url: `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases/download/v2.1.0/LuxSense-Pro-Setup-v2.1.0.exe`
        },
        portable: {
          filename: "LuxSense-Pro-v2.1.0-portable.zip",
          url: `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases/download/v2.1.0/LuxSense-Pro-v2.1.0-portable.zip`
        }
      },
      release_notes: "Production release v2.1.0 with automatic update infrastructure, SHA-256 verification, and persistent data storage."
    };
  }

  // Apply to DOM
  const tag = releaseData.tag_name || `v${releaseData.version}`;
  versionTags.forEach(el => el.textContent = tag);

  if (dateElements) {
    const d = new Date(releaseData.published_at || "2026-11-12");
    const formattedDate = d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
    dateElements.forEach(el => el.textContent = formattedDate);
  }

  const installerAsset = releaseData.assets?.installer || releaseData.assets?.["LuxSense-Pro-Setup-v2.1.0.exe"];
  if (installerAsset && installerAsset.url) {
    installerLinks.forEach(el => el.href = installerAsset.url);
  }

  const portableAsset = releaseData.assets?.portable || releaseData.assets?.["LuxSense-Pro-v2.1.0-portable.zip"];
  if (portableAsset && portableAsset.url) {
    portableLinks.forEach(el => el.href = portableAsset.url);
  }

  if (shaInstaller && installerAsset && installerAsset.sha256) {
    shaInstaller.textContent = installerAsset.sha256;
  }

  if (changelogBody && releaseData.release_notes) {
    changelogBody.innerHTML = formatMarkdown(releaseData.release_notes);
  }

  // Previous releases
  if (prevReleasesContainer && releaseData.previous_releases) {
    prevReleasesContainer.innerHTML = releaseData.previous_releases.map(pr => `
      <div class="prev-release-item" style="padding: 14px 0; border-bottom: 1px solid var(--border-color);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <strong style="color: var(--accent-green); font-family: var(--font-mono);">${pr.tag_name}</strong>
          <span style="color: var(--text-muted); font-size: 12px;">${pr.published_at?.substring(0, 10) || ''}</span>
        </div>
        <p style="font-size: 13px; color: var(--text-secondary);">${pr.description || pr.name || ''}</p>
      </div>
    `).join("");
  }
}

function parseGitHubRelease(ghData) {
  const assetsMap = {};
  let installerSha = "";

  (ghData.assets || []).forEach(a => {
    const name = a.name.toLowerCase();
    if (name.endsWith(".exe") && (name.includes("setup") || name.includes("installer"))) {
      assetsMap.installer = {
        filename: a.name,
        size: a.size,
        url: a.browser_download_url,
        sha256: ""
      };
    } else if (name.endsWith(".zip")) {
      assetsMap.portable = {
        filename: a.name,
        size: a.size,
        url: a.browser_download_url,
        sha256: ""
      };
    }
  });

  // Extract SHA from body if present
  const body = ghData.body || "";
  const lines = body.split("\n");
  for (const line of lines) {
    if (line.includes(".exe") && line.length >= 64) {
      const match = line.match(/[a-fA-F0-9]{64}/);
      if (match && assetsMap.installer) {
        assetsMap.installer.sha256 = match[0].toLowerCase();
      }
    }
  }

  return {
    version: ghData.tag_name?.replace(/^v/, ""),
    tag_name: ghData.tag_name,
    release_name: ghData.name,
    published_at: ghData.published_at,
    prerelease: ghData.prerelease,
    release_notes: ghData.body,
    assets: assetsMap
  };
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, '<h4 style="color: var(--accent-green); margin: 12px 0 6px;">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 style="color: #fff; margin: 16px 0 8px;">$1</h3>')
    .replace(/^\* (.*$)/gim, '<li style="margin-left: 18px; margin-bottom: 4px;">$1</li>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code style="background: #111419; padding: 2px 6px; border-radius: 4px; color: #21D789; font-family: var(--font-mono); font-size: 12px;">$1</code>');
  return html;
}

function initFaqAccordion() {
  const faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach(item => {
    const question = item.querySelector(".faq-question");
    question.addEventListener("click", () => {
      const isOpen = item.classList.contains("active");
      faqItems.forEach(i => i.classList.remove("active"));
      if (!isOpen) {
        item.classList.add("active");
      }
    });
  });
}

function initLiveGaugeSimulation() {
  const valEl = document.getElementById("simulated-lux-val");
  if (!valEl) return;

  let baseLux = 538.40;
  setInterval(() => {
    // Subtle realistic fluctuation of ambient lighting
    const jitter = (Math.random() - 0.5) * 2.8;
    baseLux = Math.max(10.0, baseLux + jitter);
    valEl.textContent = baseLux.toFixed(2);
  }, 1600);
}

function initMobileNav() {
  const toggle = document.querySelector(".mobile-toggle");
  const header = document.querySelector(".site-header");
  if (toggle && header) {
    toggle.addEventListener("click", () => {
      header.classList.toggle("nav-open");
    });
  }
}

function initCopyButtons() {
  const btn = document.querySelector(".sha-copy-btn");
  const val = document.getElementById("sha-installer-val");
  if (btn && val) {
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(val.textContent.trim());
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(() => btn.textContent = orig, 2000);
      } catch (e) {
        console.error("Copy failed:", e);
      }
    });
  }
}
