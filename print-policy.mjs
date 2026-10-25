/* Reprint the privacy policy PDF from the page itself.

     python build.py
     python -m http.server 8096 --directory public      (in another window)
     node print-policy.mjs
     (stop the server)  then put the size in the "(PDF, N KB)" label
     python build.py && python check.py

   Headless Chrome prints /privacyandcookiepolicy/ with its print styles,
   A4 with 15mm margins, the way the PDF has always been made (puppeteer's
   page.pdf, by hand, before 25 Oct 2026). It writes the SOURCE copy in
   assets/files/; the build copies that into public/, so a PDF written only
   to public/ is overwritten by the old one on the next build. Stop the
   server before building: while it runs it holds public/ open, and the
   build's clean-out of public/ fails half way (it did, 25 Oct 2026). Nothing
   to install: Node 22+ has fetch and WebSocket, which is all Chrome's
   DevTools protocol needs. */
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const URL_ = process.argv[2] || "http://127.0.0.1:8096/privacyandcookiepolicy/";
const OUT = "assets/files/gvn-privacy-and-cookies-policy.pdf";
const PORT = 9300 + Math.floor(Math.random() * 600);
const sleep = ms => new Promise(r => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=" + PORT,
  "--user-data-dir=" + mkdtempSync(join(tmpdir(), "gvn-print-")), "--no-first-run",
  "--no-default-browser-check", "about:blank"], { stdio: "ignore" });

async function json(path){
  for(let i = 0; i < 50; i++){
    try{ return await (await fetch("http://127.0.0.1:" + PORT + path)).json(); }
    catch(_){ await sleep(150); }
  }
  throw new Error("Chrome did not answer");
}

try{
  await json("/json/version");
  const page = (await json("/json/list")).find(t => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const wait = new Map();
  ws.onmessage = ev => { const m = JSON.parse(ev.data);
    if(m.id && wait.has(m.id)){ const w = wait.get(m.id); wait.delete(m.id); m.error ? w.rej(new Error(m.error.message)) : w.res(m.result); } };
  await new Promise(r => { ws.onopen = r; });
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; wait.set(i, { res, rej });
    ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable");
  await send("Page.navigate", { url: URL_ });
  await sleep(2500);
  const mm = 1 / 25.4;
  const pdf = await send("Page.printToPDF", {
    paperWidth: 210 * mm, paperHeight: 297 * mm,
    marginTop: 15 * mm, marginBottom: 15 * mm, marginLeft: 15 * mm, marginRight: 15 * mm,
    printBackground: true, displayHeaderFooter: false, preferCSSPageSize: false
  });
  writeFileSync(OUT, Buffer.from(pdf.data, "base64"));
  console.log("wrote " + OUT + ", " + Math.round(statSync(OUT).size / 1024) + " KB");
  ws.close();
}finally{
  chrome.kill();
}
