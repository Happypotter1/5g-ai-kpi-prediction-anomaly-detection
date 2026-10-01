"use strict";

const assert = require("node:assert/strict");
const { after, before, test } = require("node:test");
const { spawn } = require("node:child_process");
const { readFile, mkdir, writeFile } = require("node:fs/promises");
const net = require("node:net");
const path = require("node:path");
const { chromium } = require("playwright");

const projectRoot = path.resolve(__dirname, "../..");
let browser;
let server;
let baseUrl;
let serverOutput = "";
const results = [];
const evidenceDir = process.env.E2E_ARTIFACT_DIR;
const runStarted = new Date().toISOString();

// The same interactions run against a new local process or the deployed public app.
function acceptanceTest(name, run) {
  test(name, async () => {
    const started = Date.now();
    try {
      await run();
      results.push({ name, status: "passed", durationMs: Date.now() - started });
    } catch (error) {
      results.push({ name, status: "failed", durationMs: Date.now() - started, error: error.message });
      throw error;
    }
  });
}

async function saveEvidence(page, filename) {
  if (evidenceDir) {
    const ui = process.env.BASE_URL ? page.frameLocator('iframe[title="streamlitApp"]') : page;
    const title = ui.getByRole("heading", { name: "5G KPI 智能运维平台" });
    if (await title.isVisible()) await title.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(evidenceDir, filename), fullPage: true });
  }
}

async function waitForRendered(ui) {
  // Cloud reruns arrive in several messages. A new metric alone does not mean
  // that the download button below it has received the matching CSV yet.
  await ui.waitForFunction(() => !document.querySelector('[data-stale="true"]')
    && !document.querySelector('[data-testid="stStatusWidget"]'), undefined, { timeout: 60_000 });
}

async function freePort() {
  return new Promise((resolve, reject) => {
    const listener = net.createServer();
    listener.once("error", reject);
    listener.listen(0, "127.0.0.1", () => {
      const port = listener.address().port;
      listener.close(() => resolve(port));
    });
  });
}

async function waitForHealth(url, processHandle) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (processHandle.exitCode !== null) {
      throw new Error(`Streamlit exited with code ${processHandle.exitCode}: ${serverOutput.slice(-2000)}`);
    }
    try {
      const response = await fetch(`${url}/_stcore/health`);
      if (response.ok) return;
    } catch { /* Server is still starting. */ }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Streamlit health endpoint did not become ready: ${serverOutput.slice(-2000)}`);
}

before(async () => {
  if (evidenceDir) await mkdir(evidenceDir, { recursive: true });
  browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || undefined, headless: true });
  if (process.env.BASE_URL) {
    const target = new URL(process.env.BASE_URL);
    assert.equal(target.protocol, "https:", "Public acceptance requires an HTTPS target");
    baseUrl = target.href.replace(/\/$/, "");
    // Streamlit Community Cloud may sleep between visits; wake it through its UI.
    const page = await browser.newPage();
    try {
      await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
      const deadline = Date.now() + 180_000;
      while (Date.now() < deadline) {
        const hosted = page.frameLocator('iframe[title="streamlitApp"]');
        if (await hosted.getByRole("heading", { name: "5G KPI 智能运维平台" }).isVisible()) return;
        const wake = page.getByRole("button", { name: "Yes, get this app back up!" });
        if (await wake.isVisible()) await wake.click();
        try {
          await hosted.getByRole("heading", { name: "5G KPI 智能运维平台" }).waitFor({ timeout: 10_000 });
          return;
        } catch { /* Continue while the hosted app is starting. */ }
      }
      await saveEvidence(page, "startup-failure.png");
      throw new Error("Public Streamlit application did not become ready within 180 seconds");
    } finally {
      await page.close();
    }
  }
  const port = await freePort();
  baseUrl = `http://127.0.0.1:${port}`;
  const python = process.env.PYTHON || path.join(projectRoot, ".venv", "Scripts", "python.exe");
  server = spawn(python, [
    "-m", "streamlit", "run", "week7/app.py", "--server.headless", "true",
    "--server.address", "127.0.0.1", "--server.port", String(port),
    "--browser.gatherUsageStats", "false",
  ], { cwd: projectRoot, stdio: ["ignore", "pipe", "pipe"] });
  for (const stream of [server.stdout, server.stderr]) {
    stream.on("data", (chunk) => { serverOutput = (serverOutput + chunk.toString()).slice(-4000); });
  }
  if (!server.pid) throw new Error(`Could not start Python at ${python}`);
  await waitForHealth(baseUrl, server);
});

after(async () => {
  if (evidenceDir) {
    await writeFile(path.join(evidenceDir, "results.json"), JSON.stringify({
      startedAt: runStarted, finishedAt: new Date().toISOString(),
      target: baseUrl, scope: process.env.BASE_URL ? "public-cloud" : "local",
      browserChannel: process.env.BROWSER_CHANNEL || "chromium", browserVersion: browser?.version(),
      passed: results.filter((item) => item.status === "passed").length,
      failed: results.filter((item) => item.status === "failed").length,
      tests: results,
    }, null, 2) + "\n");
  }
  if (browser) await browser.close();
  if (server && server.exitCode === null) server.kill();
});

async function openApp(page) {
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
  // Community Cloud wraps the app in an iframe; local Streamlit serves it directly.
  const frameElement = process.env.BASE_URL
    ? await page.waitForSelector('iframe[title="streamlitApp"]', { timeout: 60_000 }) : null;
  const ui = frameElement ? await frameElement.contentFrame() : page;
  assert(ui, "Streamlit application frame is present");
  await ui.getByRole("heading", { name: "5G KPI 智能运维平台" }).waitFor({ timeout: 60_000 });
  await ui.getByText("数据与模型结果已就绪").waitFor();
  // Sidebar readiness appears before cached data and home metrics finish rendering.
  await ui.waitForFunction(() => [...document.querySelectorAll('[data-testid="stMetric"]')]
    .some((item) => item.innerText.includes("8 个")), undefined, { timeout: 60_000 });
  assert.equal(await ui.locator('[data-testid="stException"]').count(), 0);
  return ui;
}

async function navigate(page, name) {
  await page.locator('[data-testid="stSidebar"]').getByText(name, { exact: true }).click();
  const heading = name === "数据浏览" ? "KPI 数据浏览" : name;
  await page.getByRole("heading", { name: heading, exact: true }).waitFor({ timeout: 30_000 });
  assert.equal(await page.locator('[data-testid="stException"]').count(), 0);
}

acceptanceTest("home and prediction controls work in a real browser", async () => {
  const page = await browser.newPage({ acceptDownloads: true, viewport: { width: 1440, height: 1400 } });
  try {
    const ui = await openApp(page);
    const metrics = await ui.locator('[data-testid="stMetric"]').allInnerTexts();
    assert(metrics.some((value) => value.includes("8 个")));
    assert(metrics.some((value) => value.includes("40 / 840")));
    await navigate(ui, "KPI 预测");
    await ui.locator('[data-testid="stSelectbox"]').first().click();
    await ui.getByText("Transformer（全网平均 KPI）", { exact: true }).last().click();
    await ui.locator('[data-testid="stPlotlyChart"]').getByText("Transformer", { exact: true }).waitFor();
    await waitForRendered(ui);
    await ui.getByRole("button", { name: "下载当前预测结果" }).waitFor({ timeout: 30_000 });
    const downloadPromise = page.waitForEvent("download");
    await ui.getByRole("button", { name: "下载当前预测结果" }).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), "kpi_predictions.csv");
    const csv = await readFile(await download.path(), "utf8");
    if (evidenceDir) await writeFile(path.join(evidenceDir, "prediction-download.csv"), csv);
    assert(csv.split(/\r?\n/, 1)[0].includes("Transformer"));
  } finally {
    await saveEvidence(page, "01-prediction.png");
    await page.close();
  }
});

acceptanceTest("anomaly strategy changes count and explains statistical zero", async () => {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  try {
    const ui = await openApp(page);
    await navigate(ui, "异常检测");
    let metrics = await ui.locator('[data-testid="stMetric"]').allInnerTexts();
    assert(metrics.some((value) => /异常时刻\s*40/.test(value)));
    await ui.getByRole("heading", { name: "为什么 3σ 和 IQR 都是 0？" }).waitFor();
    await ui.getByText("2880 个 KPI 的平均值", { exact: false }).waitFor();
    await ui.locator('[data-testid="stSelectbox"]').first().click();
    await ui.getByText("共同异常（高置信）", { exact: true }).last().click();
    await ui.waitForFunction(() => [...document.querySelectorAll('[data-testid="stMetric"]')].some((item) => /异常时刻\s*17/.test(item.innerText)));
    metrics = await ui.locator('[data-testid="stMetric"]').allInnerTexts();
    assert(metrics.some((value) => /异常时刻\s*17/.test(value)));
    await waitForRendered(ui);
  } finally {
    await saveEvidence(page, "02-anomaly.png");
    await page.close();
  }
});

acceptanceTest("root-cause definitions and Top N slider render", async () => {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  try {
    const ui = await openApp(page);
    await navigate(ui, "根因分析");
    await ui.getByRole("heading", { name: "根因候选指标如何理解" }).waitFor();
    await ui.getByText("contribution_score =", { exact: false }).waitFor();
    const slider = ui.getByRole("slider").first();
    await slider.focus();
    await slider.press("Home");
    assert.equal(await slider.inputValue(), "5");
    await ui.waitForFunction(() => document.querySelectorAll('[data-testid="stPlotlyChart"] .yaxislayer-above .ytick').length === 5);
    await waitForRendered(ui);
    assert.equal(await ui.locator('[data-testid="stException"]').count(), 0);
  } finally {
    await saveEvidence(page, "03-root-causes.png");
    await page.close();
  }
});

acceptanceTest("data browser selection and CSV download work", async () => {
  const page = await browser.newPage({ acceptDownloads: true, viewport: { width: 1440, height: 1400 } });
  try {
    const ui = await openApp(page);
    await navigate(ui, "数据浏览");
    await ui.locator('[data-testid="stMetric"]').first().waitFor({ timeout: 60_000 });
    const metrics = await ui.locator('[data-testid="stMetric"]').allInnerTexts();
    assert(metrics.some((value) => /样本数\s*840/.test(value)));
    const initialMean = metrics.find((value) => value.startsWith("平均值"));
    await ui.locator('[data-testid="stSelectbox"]').first().click();
    await ui.getByRole("combobox", { name: "选择 KPI（格式：小区_扇区_Beam）" }).fill("11_0_19");
    await ui.getByRole("option", { name: "11_0_19" }).click();
    await ui.waitForFunction((oldMean) => {
      const current = [...document.querySelectorAll('[data-testid="stMetric"]')]
        .map((element) => element.innerText).find((value) => value.startsWith("平均值"));
      return current && current !== oldMean;
    }, initialMean);
    const startSlider = ui.getByRole("slider", { name: "时间范围 — start" });
    await startSlider.focus();
    await startSlider.press("ArrowRight");
    await ui.waitForFunction(() => [...document.querySelectorAll('[data-testid="stMetric"]')]
      .some((element) => /样本数\s*839/.test(element.innerText)));
    await waitForRendered(ui);
    const downloadPromise = page.waitForEvent("download");
    await ui.getByRole("button", { name: "下载当前 KPI" }).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), "kpi_11_0_19.csv");
    const csv = await readFile(await download.path(), "utf8");
    if (evidenceDir) await writeFile(path.join(evidenceDir, "kpi-download.csv"), csv);
    assert(csv.split(/\r?\n/).some((line) => line.includes("11_0_19")));
    assert.equal(csv.trimEnd().split(/\r?\n/).length, 840); // Header + 839 selected rows.
  } finally {
    await saveEvidence(page, "04-data-browser.png");
    await page.close();
  }
});
