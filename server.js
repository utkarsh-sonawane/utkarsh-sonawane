import { readFileSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { createServer } from "node:http";
import { extname, resolve, relative, isAbsolute } from "node:path";
import { marked } from "marked";

const README_PATH = "README.md";
const ASSETS_ROOT = resolve(".", "assets");

const MIME = {
  ".svg":  "image/svg+xml",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".json": "application/json",
};

/** Try to serve a static file from assets/. Returns true if handled. */
function serveStatic(req, res) {
  let pathname;
  try {
    pathname = decodeURIComponent((req.url || "/").split("?")[0].split("#")[0]);
  } catch {
    return false;
  }

  // Only handle routes under /assets/
  if (!pathname.startsWith("/assets/")) return false;

  const subpath = pathname.slice("/assets/".length);
  const safePath = resolve(ASSETS_ROOT, subpath);

  // Containment check: verify resolved path is strictly within ASSETS_ROOT
  const rel = relative(ASSETS_ROOT, safePath);
  if (rel === "" || rel.startsWith("..") || isAbsolute(rel)) {
    res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Forbidden");
    return true;
  }

  const ext = extname(safePath).toLowerCase();
  const mime = MIME[ext];
  if (!mime) {
    res.writeHead(415, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Unsupported Media Type");
    return true;
  }

  try {
    if (!existsSync(safePath)) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not Found");
      return true;
    }
    const data = readFileSync(safePath);
    res.writeHead(200, { "Content-Type": mime });
    res.end(data);
    return true;
  } catch {
    return false;
  }
}

function renderPage(theme = "auto") {
  const markdown = readFileSync(README_PATH, "utf8");
  const body = marked.parse(markdown);
  return `<!doctype html>
<html lang="en" data-theme="${theme}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>sonawaneutkarsh — GitHub Profile README</title>
<style>
  :root {
    color-scheme: light dark;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
  }
  .banner {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 10px 24px;
    font-size: 13px;
    color: #8b949e;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .banner a { color: #58a6ff; text-decoration: none; }
  .banner a:hover { text-decoration: underline; }
  .theme-toggle a {
    margin-left: 12px;
    padding: 2px 8px;
    border: 1px solid #30363d;
    border-radius: 4px;
    font-size: 12px;
  }
  .container {
    max-width: 920px;
    margin: 0 auto;
    padding: 32px 24px 64px;
  }
  h1, h2, h3, h4 { border-bottom: 1px solid #21262d; padding-bottom: 0.3em; margin-top: 1.5em; }
  h1:first-child { margin-top: 0; }
  a { color: #58a6ff; }
  img { max-width: 100%; height: auto; }
  code, samp {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0.2em 0.4em;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.9em;
  }
  blockquote {
    border-left: 4px solid #30363d;
    margin: 1em 0;
    padding: 0 1em;
    color: #8b949e;
  }

  /* Light theme overrides */
  html[data-theme="light"],
  @media (prefers-color-scheme: light) {
    html:not([data-theme="dark"]) body {
      background: #ffffff;
      color: #1f2328;
    }
    html:not([data-theme="dark"]) .banner {
      background: #f6f8fa;
      border-bottom: 1px solid #d0d7de;
      color: #656d76;
    }
    html:not([data-theme="dark"]) a { color: #0969da; }
    html:not([data-theme="dark"]) code, html:not([data-theme="dark"]) samp {
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      color: #1f2328;
    }
    html:not([data-theme="dark"]) blockquote {
      border-left: 4px solid #d0d7de;
      color: #656d76;
    }
    html:not([data-theme="dark"]) .theme-toggle a {
      border-color: #d0d7de;
    }
  }

  html[data-theme="light"] body {
    background: #ffffff !important;
    color: #1f2328 !important;
  }
  html[data-theme="light"] .banner {
    background: #f6f8fa !important;
    border-bottom: 1px solid #d0d7de !important;
    color: #656d76 !important;
  }
  html[data-theme="light"] a { color: #0969da !important; }
  html[data-theme="light"] code, html[data-theme="light"] samp {
    background: #f6f8fa !important;
    border: 1px solid #d0d7de !important;
    color: #1f2328 !important;
  }
  html[data-theme="light"] blockquote {
    border-left: 4px solid #d0d7de !important;
    color: #656d76 !important;
  }
  html[data-theme="light"] .theme-toggle a {
    border-color: #d0d7de !important;
  }
</style>
</head>
<body>
  <div class="banner">
    <div>Previewing <strong>README.md</strong> of <a href="https://github.com/sonawaneutkarsh/sonawaneutkarsh">sonawaneutkarsh/sonawaneutkarsh</a></div>
    <div class="theme-toggle">
      <a href="?theme=dark">Dark</a>
      <a href="?theme=light">Light</a>
      <a href="?theme=auto">Auto</a>
    </div>
  </div>
  <main class="container">
${body}
  </main>
</body>
</html>
`;
}

if (process.argv.includes("--build")) {
  try {
    mkdirSync("dist", { recursive: true });
    writeFileSync("dist/index.html", renderPage("dark"));
    writeFileSync("dist/index-light.html", renderPage("light"));
    console.log("Built dist/index.html (dark) and dist/index-light.html (light)");
  } catch (err) {
    console.error("Build failed.");
    console.error(err);
    process.exitCode = 1;
  }
} else {
  const port = Number(process.env.PORT) || 3000;
  const server = createServer((req, res) => {
    try {
      if (serveStatic(req, res)) return;
      const parsedUrl = new URL(req.url || "/", "http://127.0.0.1");
      const theme = parsedUrl.searchParams.get("theme") || "dark";
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(renderPage(theme));
    } catch (err) {
      console.error(err);
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Failed to render README preview.");
    }
  });
  const host = process.env.HOST || "127.0.0.1";
  server.listen(port, host, () => {
    console.log(`Serving README preview on http://${host}:${port}`);
  });
}
