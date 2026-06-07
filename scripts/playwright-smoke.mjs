import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));

const appUrl = process.env.APP_URL || "http://127.0.0.1:5173";
const apiUrl = process.env.API_URL || "http://127.0.0.1:8000/api";
const saveScreenshots = process.env.PW_SCREENSHOTS === "1";
const screenshotDir = resolve(scriptDir, "../docs/playwright-confirmation");
const viewportWidth = Number(process.env.PW_VIEWPORT_WIDTH || 1274);
const viewportHeight = Number(process.env.PW_VIEWPORT_HEIGHT || 1000);
const letterPrintableWidthPx = 8 * 96;
const letterPrintableHeightPx = 10.5 * 96;

async function screenshot(page, name) {
  if (!saveScreenshots) return;
  await mkdir(screenshotDir, { recursive: true });
  await page.screenshot({ path: resolve(screenshotDir, `${name}.png`), fullPage: true });
}

const beforeProjects = await fetch(`${apiUrl}/projects`).then((response) => response.json());
const maxProjectIdBefore = Math.max(0, ...beforeProjects.map((project) => project.id));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: viewportWidth, height: viewportHeight }, acceptDownloads: true });
const checks = [];

try {
  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.locator("h1", { hasText: "Engineering Dashboard" }).waitFor({ timeout: 8000 });
  if (await page.getByText("Role: Engineer").count()) {
    throw new Error("Excluded role chip is visible");
  }
  const dashboardHeaders = await page.locator(".table-panel").first().locator("thead th").allTextContents();
  if (dashboardHeaders.includes("Status")) {
    throw new Error("Dashboard recent-calculations Status column is visible");
  }
  if (await page.locator(".table-toolbar .filter-select").count()) {
    throw new Error("Dashboard status filter dropdown is visible");
  }
  await screenshot(page, "dashboard");
  checks.push("Dashboard loaded");

  await page.getByRole("button", { name: "Standards Tables", exact: true }).click();
  await page.locator("h1", { hasText: "Standards & Lookup Tables" }).waitFor({ timeout: 8000 });
  await page.getByRole("columnheader", { name: "D (in)", exact: true }).waitFor({ timeout: 8000 });
  await page.getByRole("columnheader", { name: "tw Options (in)", exact: true }).waitFor({ timeout: 8000 });
  await page.getByRole("columnheader", { name: "R", exact: true }).waitFor({ timeout: 8000 });
  if (await page.getByRole("columnheader", { name: "Source", exact: true }).count()) {
    throw new Error("Standards tables still show Source columns");
  }
  const dropdownOptionsText = await page.locator(".standard-section", { hasText: "Dropdown Options" }).textContent();
  if (dropdownOptionsText?.includes("Calculation Statuses") || dropdownOptionsText?.includes("Project Statuses")) {
    throw new Error("Status dropdown lists are still visible in Standards dropdown options");
  }
  await screenshot(page, "standards-tables");
  checks.push("Standards page uses readable lookup tables without status-only dropdown lists");

  await page.getByRole("button", { name: "References", exact: true }).click();
  await page.locator("h1", { hasText: "References" }).waitFor({ timeout: 8000 });
  if (await page.locator(".reference-row").getByRole("button", { name: "Open" }).count()) {
    throw new Error("References tab still shows Open buttons");
  }
  checks.push("References tab has no Open buttons");

  await page.getByRole("button", { name: "Dashboard", exact: true }).click();
  await page.locator("h1", { hasText: "Engineering Dashboard" }).waitFor({ timeout: 8000 });

  const recentCount = await page.locator(".project-card.clickable").count();
  if (recentCount > 0) {
    await page.locator(".project-card.clickable").first().click();
    await page.getByText("Project Information").waitFor({ timeout: 8000 });
    await screenshot(page, "project-detail-from-dashboard");
    checks.push("Recent project card opens Project Detail");
  }

  await page.getByRole("button", { name: "Projects", exact: true }).click();
  await page.locator("h1", { hasText: "Projects" }).waitFor({ timeout: 8000 });
  await page.locator('.project-table .icon-actions button[title="Delete"]').first().waitFor({ timeout: 8000 });
  await screenshot(page, "projects");
  checks.push("Projects page loaded with project delete actions");

  const rowCheckboxCount = await page.locator('.project-table tbody input[type="checkbox"]').count();
  if (rowCheckboxCount > 0) {
    await page.locator('.project-table tbody input[type="checkbox"]').first().check();
    await page.getByText("1 selected").waitFor({ timeout: 4000 });
    checks.push("Project row selection updates selected count");
  }

  await page.getByRole("button", { name: "New Project", exact: true }).click();
  await page.getByText("Project Information").waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "Calculations", exact: true }).waitFor({ timeout: 8000 });
  const createdProjectName = (await page.locator(".project-detail-header h1").textContent())?.trim();
  await screenshot(page, "new-project-detail");
  checks.push("New Project navigates to Project Detail");

  await page.getByRole("button", { name: "New Highway Calc", exact: true }).click();
  await page.getByText("Calculation Metadata").waitFor({ timeout: 8000 });
  await page.getByText("Pipeline Geometry").waitFor({ timeout: 8000 });
  await page.locator(".loading-tabs button.active", { hasText: "Highway Loading" }).waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "F. Highway Loading", exact: true }).waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "Results Summary", exact: true }).waitFor({ timeout: 8000 });
  await page.getByRole("cell", { name: "Barlow Stress", exact: true }).waitFor({ timeout: 8000 });
  await page.locator('[aria-label="Nominal Pipe Diameter (NPS) help"]').focus();
  await page.getByText("Nominal pipe size. The outside diameter and wall thickness options update from the standards tables.").waitFor({ timeout: 4000 });
  await page.locator("label.field", { hasText: "Nominal Pipe Diameter" }).locator("select").selectOption("16");
  await page.locator("label.field", { hasText: "Pipe Outside Diameter" }).locator("input").waitFor({ timeout: 4000 });
  const wallThicknessField = page.locator("label.field", { hasText: "Wall Thickness tw" });
  const wallThicknessInput = wallThicknessField.locator("input");
  const wallThicknessToggle = wallThicknessField.locator(".combo-toggle");
  await wallThicknessToggle.waitFor({ timeout: 4000 });
  await wallThicknessToggle.click();
  await wallThicknessField.locator(".combo-option", { hasText: "0.5" }).click();
  if ((await wallThicknessInput.inputValue()) !== "0.5") {
    throw new Error("Wall thickness dropdown option did not populate the input");
  }
  await wallThicknessInput.fill("0.377");
  await page.locator(".warning-callout", { hasText: "Wall thickness is not listed for the selected NPS standards table" }).waitFor({ timeout: 8000 });
  await page.locator("label.field", { hasText: "Pipe Depth / Cover H" }).locator("input").fill("40");
  await page.locator(".warning-callout", { hasText: "Cover depth is outside workbook-supported range 1 to 30 ft." }).waitFor({ timeout: 8000 });
  const worksheetGeometry = await page.locator(".diagram").first().evaluate((element) => {
    const surface = element.querySelector(".diagram-surface")?.getBoundingClientRect();
    const bore = element.querySelector(".diagram-bore")?.getBoundingClientRect();
    const pipe = element.querySelector(".diagram-pipe")?.getBoundingClientRect();
    const cover = element.querySelector(".diagram-cover")?.getBoundingClientRect();
    const coverLabel = element.querySelector(".diagram-cover span")?.getBoundingClientRect();
    const soilLabel = element.querySelector(".diagram-soil span")?.getBoundingClientRect();
    const wheel = element.querySelector(".vehicle-wheel.front")?.getBoundingClientRect();
    const overlaps = coverLabel && soilLabel
      ? !(coverLabel.right < soilLabel.left || coverLabel.left > soilLabel.right || coverLabel.bottom < soilLabel.top || coverLabel.top > soilLabel.bottom)
      : true;
    return {
      bore: bore ? Math.abs(bore.width - bore.height) : 999,
      pipe: pipe ? Math.abs(pipe.width - pipe.height) : 999,
      coverToPipeTop: cover && pipe ? Math.abs(cover.bottom - pipe.top) : 999,
      coverStartsAboveSurface: cover && surface ? cover.top < surface.top - 1 : true,
      wheelToRoad: wheel && surface ? Math.abs(wheel.bottom - surface.top) : 999,
      labelsOverlap: overlaps
    };
  });
  if (worksheetGeometry.bore > 1 || worksheetGeometry.pipe > 1) {
    throw new Error("Worksheet schematic pipe and bore are not circular");
  }
  if (worksheetGeometry.coverToPipeTop > 2) {
    throw new Error("Worksheet schematic cover dimension does not terminate at the top of pipe");
  }
  if (worksheetGeometry.coverStartsAboveSurface) {
    throw new Error("Worksheet schematic cover dimension extends above the road surface");
  }
  if (worksheetGeometry.wheelToRoad > 2) {
    throw new Error("Highway vehicle wheels are not seated on the road surface");
  }
  if (worksheetGeometry.labelsOverlap) {
    throw new Error("Worksheet schematic depth and soil labels overlap");
  }
  await screenshot(page, "calculation-worksheet");
  checks.push("New highway calculation opens calculated worksheet with tooltips, custom wall thickness, and warnings");

  await page.getByRole("button", { name: "Report", exact: true }).click();
  await page.getByText("Back to Calculation").waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "Project & Calculation", exact: true }).waitFor({ timeout: 8000 });
  await page.locator(".report-schematic .diagram-pipe").waitFor({ timeout: 8000 });
  await page.emulateMedia({ media: "print" });
  const toolbarDisplay = await page.locator(".report-toolbar").evaluate((element) => getComputedStyle(element).display);
  const reportDisplay = await page.locator(".report-page").evaluate((element) => getComputedStyle(element).display);
  const reportMetrics = await page.locator(".report-page").evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const schematic = element.querySelector(".report-schematic .diagram-pipe")?.getBoundingClientRect();
    return {
      width: rect.width,
      height: rect.height,
      clientWidth: element.clientWidth,
      clientHeight: element.clientHeight,
      scrollWidth: element.scrollWidth,
      scrollHeight: element.scrollHeight,
      schematicVisible: Boolean(schematic && schematic.width > 0 && schematic.height > 0)
    };
  });
  if (toolbarDisplay !== "none" || reportDisplay === "none") {
    throw new Error("Report print CSS is not ready");
  }
  if (reportMetrics.width > letterPrintableWidthPx + 1 || reportMetrics.height > letterPrintableHeightPx + 1) {
    throw new Error(`Report print box exceeds letter printable area: ${reportMetrics.width}x${reportMetrics.height}px`);
  }
  if (reportMetrics.scrollWidth > reportMetrics.clientWidth + 1 || reportMetrics.scrollHeight > reportMetrics.clientHeight + 1) {
    throw new Error(`Report print content overflows: client ${reportMetrics.clientWidth}x${reportMetrics.clientHeight}, scroll ${reportMetrics.scrollWidth}x${reportMetrics.scrollHeight}`);
  }
  if (!reportMetrics.schematicVisible) {
    throw new Error("Report schematic is not visible in print mode");
  }
  const pdf = await page.pdf({ format: "Letter", printBackground: true, preferCSSPageSize: true });
  const pdfPageCount = (pdf.toString("latin1").match(/\/Type\s*\/Page\b/g) || []).length;
  if (pdfPageCount !== 1) {
    throw new Error(`Report browser PDF should be exactly one page, got ${pdfPageCount}`);
  }
  await page.emulateMedia({ media: "screen" });
  if (await page.getByText("Acknowledgment required to finalize").count()) {
    throw new Error("Excluded acknowledgment text is visible");
  }
  await page.getByRole("button", { name: "Detailed", exact: true }).click();
  await page.getByText("Formula Trace").waitFor({ timeout: 8000 });
  const detailedDownloadPromise = page.waitForEvent("download", { timeout: 15000 });
  await page.getByRole("button", { name: "Generate Detailed PDF", exact: true }).click();
  const detailedDownload = await detailedDownloadPromise;
  if (!detailedDownload.suggestedFilename().includes("detailed")) {
    throw new Error(`Detailed PDF download filename is unexpected: ${detailedDownload.suggestedFilename()}`);
  }
  checks.push("Detailed backend PDF generates for the selected scenario");
  await screenshot(page, "report-preview");
  checks.push("Report preview opens with print-ready schematic and paper layout");

  await page.getByRole("button", { name: "Back to Calculation", exact: true }).click();
  await page.locator("label.field", { hasText: "Operating Pressure P" }).locator("input").fill("-20");
  await page.locator(".warning-callout", { hasText: "Operating pressure cannot be below 0 psia" }).waitFor({ timeout: 8000 });
  await page.getByRole("button", { name: "Report", exact: true }).click();
  await page.getByRole("button", { name: "Detailed", exact: true }).click();
  await page.getByRole("button", { name: "Generate Detailed PDF", exact: true }).click();
  await page.locator(".detailed-report-error", { hasText: "Detailed PDF generation is blocked" }).waitFor({ timeout: 12000 });
  await page.getByRole("button", { name: "Recalculate Scenario", exact: true }).waitFor({ timeout: 8000 });
  checks.push("Detailed report generation blocks invalid selected scenarios with recovery action");

  await page.getByRole("button", { name: "Back to Calculation", exact: true }).click();
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page.getByText("Project Information").waitFor({ timeout: 8000 });
  await page.getByRole("button", { name: "New Railroad Calc", exact: true }).click();
  await page.getByText("Calculation Metadata").waitFor({ timeout: 8000 });
  await page.locator(".loading-tabs button.active", { hasText: "Railroad Loading" }).waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "F. Railroad Loading", exact: true }).waitFor({ timeout: 8000 });
  await page.getByText("Applied Design Surface Pressure").waitFor({ timeout: 8000 });
  await page.getByRole("heading", { name: "Results Summary", exact: true }).waitFor({ timeout: 8000 });
  const railroadGeometry = await page.locator(".diagram").first().evaluate((element) => {
    const coverLabel = element.querySelector(".diagram-cover span")?.getBoundingClientRect();
    const soilLabel = element.querySelector(".diagram-soil span")?.getBoundingClientRect();
    const wheel = element.querySelector(".train-wheel.a")?.getBoundingClientRect();
    const upperRail = element.querySelectorAll(".diagram-track span")[0]?.getBoundingClientRect();
    const overlaps = coverLabel && soilLabel
      ? !(coverLabel.right < soilLabel.left || coverLabel.left > soilLabel.right || coverLabel.bottom < soilLabel.top || coverLabel.top > soilLabel.bottom)
      : true;
    return {
      wheelToRail: wheel && upperRail ? Math.abs(wheel.bottom - upperRail.bottom) : 999,
      labelsOverlap: overlaps
    };
  });
  if (railroadGeometry.wheelToRail > 4) {
    throw new Error("Railroad wheels are not seated on the rail surface");
  }
  if (railroadGeometry.labelsOverlap) {
    throw new Error("Railroad schematic depth and soil labels overlap");
  }
  await screenshot(page, "railroad-calculation-worksheet");
  checks.push("New railroad calculation opens calculated worksheet");

  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page.getByText("Project Information").waitFor({ timeout: 8000 });
  const calcRowsBeforeCancel = await page.locator(".project-calcs-table tbody tr").count();
  page.once("dialog", async (dialog) => {
    if (!dialog.message().includes("Delete this calculation")) {
      throw new Error(`Unexpected calculation delete dialog: ${dialog.message()}`);
    }
    await dialog.dismiss();
  });
  await page.locator('.project-calcs-table .icon-actions button[title="Delete Calculation"]').first().click();
  if (await page.locator(".project-calcs-table tbody tr").count() !== calcRowsBeforeCancel) {
    throw new Error("Dismissing single calculation delete removed a row");
  }
  page.once("dialog", async (dialog) => {
    if (!dialog.message().includes("Delete 2 selected calculations")) {
      throw new Error(`Unexpected bulk calculation delete dialog: ${dialog.message()}`);
    }
    await dialog.accept();
  });
  await page.locator('.project-calcs-table thead input[type="checkbox"]').check();
  await page.getByRole("button", { name: "Delete Selected Calculations", exact: true }).click();
  await page.locator(".empty-calcs").waitFor({ timeout: 8000 });
  checks.push("Bulk calculation delete confirmation removes selected calculation rows");

  await page.getByRole("button", { name: "Projects", exact: true }).click();
  await page.locator("h1", { hasText: "Projects" }).waitFor({ timeout: 8000 });
  const createdProjectRow = page.locator(".project-table tbody tr", { hasText: createdProjectName || "" });
  await createdProjectRow.waitFor({ timeout: 8000 });
  page.once("dialog", async (dialog) => {
    if (!dialog.message().includes("Delete this project")) {
      throw new Error(`Unexpected project delete dialog: ${dialog.message()}`);
    }
    await dialog.dismiss();
  });
  await createdProjectRow.locator('.icon-actions button[title="Delete"]').click();
  await createdProjectRow.waitFor({ timeout: 8000 });
  await page.getByRole("button", { name: "New Project", exact: true }).click();
  await page.getByText("Project Information").waitFor({ timeout: 8000 });
  const secondProjectName = (await page.locator(".project-detail-header h1").textContent())?.trim();
  await page.getByRole("button", { name: "Projects", exact: true }).click();
  await page.locator("h1", { hasText: "Projects" }).waitFor({ timeout: 8000 });
  const firstBulkProjectRow = page.locator(".project-table tbody tr", { hasText: createdProjectName || "" });
  const secondBulkProjectRow = page.locator(".project-table tbody tr", { hasText: secondProjectName || "" });
  await firstBulkProjectRow.locator('input[type="checkbox"]').check();
  await secondBulkProjectRow.locator('input[type="checkbox"]').check();
  page.once("dialog", async (dialog) => {
    if (!dialog.message().includes("Delete 2 selected projects")) {
      throw new Error(`Unexpected bulk project delete dialog: ${dialog.message()}`);
    }
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Delete Selected", exact: true }).click();
  await firstBulkProjectRow.waitFor({ state: "detached", timeout: 8000 });
  await secondBulkProjectRow.waitFor({ state: "detached", timeout: 8000 });
  checks.push("Single project delete can cancel, and bulk project delete removes selected rows");

  console.log(JSON.stringify({ ok: true, checks }, null, 2));
} finally {
  await browser.close();
  const afterProjects = await fetch(`${apiUrl}/projects`).then((response) => response.json());
  for (const project of afterProjects.filter((item) => item.id > maxProjectIdBefore)) {
    await fetch(`${apiUrl}/projects/${project.id}`, { method: "DELETE" });
  }
}
