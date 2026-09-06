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

function renderPage() {
  const markdown = readFileSync(README_PATH, "utf8");
  const body = marked.parse(markdown);
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>sonawaneutkarsh — GitHub Profile README</title>
<style>
  :root {
    color-scheme: dark;
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
  }
  .banner a { color: #58a6ff; text-decoration: none; }
  .banner a:hover { text-decoration: underline; }
  .container {
    max-width: 920px;
    margin: 0 auto;
    padding: 32px 24px 64px;
  }
  h1, h2, h3, h4 { border-bottom: 1px solid #21262d; padding-bottom: 0.3em; margin-top: 1.5em; }
  h1:first-child { margin-top: 0; }
  a { color: #58a6ff; }
  img { max-width: 100%; }
  picture img { max-width: 100%; }
  code, samp {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0.2em 0.4em;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.9em;
  }
  pre {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 16px;
    overflow: auto;
  }
  pre code { background: none; border: none; padding: 0; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
  }
  th, td {
    border: 1px solid #30363d;
    padding: 8px 12px;
    text-align: left;
    vertical-align: top;
  }
  th { background: #161b22; }
  blockquote {
    border-left: 4px solid #30363d;
    margin: 1em 0;
    padding: 0 1em;
    color: #8b949e;
  }
  hr { border: none; border-top: 1px solid #21262d; margin: 2em 0; }
  sub { color: #8b949e; }
  sub a { color: #58a6ff; }
</style>
</head>
<body>
  <div class="banner">Previewing <strong>README.md</strong> of <a href="https://github.com/sonawaneutkarsh/sonawaneutkarsh">sonawaneutkarsh/sonawaneutkarsh</a></div>
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
    writeFileSync("dist/index.html", renderPage());
    console.log("Built dist/index.html");
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
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(renderPage());
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
