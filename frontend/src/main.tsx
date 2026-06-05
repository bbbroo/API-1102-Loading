import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowLeft,
  Calculator,
  Car,
  Copy,
  Database,
  Download,
  FileDown,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  FolderPlus,
  Gauge,
  Layers,
  Plus,
  Printer,
  RailSymbol,
  Ruler,
  ShieldCheck,
  Table2,
  Trash2,
  Upload
} from "lucide-react";
import hdrLogo from "./assets/hdr-logo.svg";
import { api } from "./api/client";
import {
  AppShell,
  Button,
  Field,
  MetricCard,
  PageKey,
  PageTitle,
  Panel,
  ResultBadge,
  SearchBox,
  SectionHeader,
  StatusPill,
  UtilizationBar
} from "./components/ui";
import type { Calculation, DashboardSummary, ExportRecord, Project, Scenario } from "./types";
import "./styles.css";

type StandardsPayload = Record<string, any>;
type LoadingMode = "highway" | "railroad";

const statusOptions = ["Draft", "For Review", "Reviewed", "Issued", "Superseded", "Void", "Archive"];
const projectStatuses = ["Active", "On Hold", "Complete", "Archived"];
const fieldHelp: Record<string, string> = {
  project_name: "Use the project name your team will recognize in exports, reports, and dashboard searches.",
  project_number: "Optional internal or client project identifier used for report traceability.",
  client: "Client or owner associated with this crossing package.",
  location: "General crossing location, city, state, milepost, or project corridor.",
  calc_number: "Unique calculation identifier for this crossing and revision.",
  crossing_name: "Name of the road, railroad, or crossing feature being analyzed.",
  route: "Route, road, highway, railroad, or subdivision name for the loading source.",
  revision: "Documentation revision shown in reports and exports.",
  status: "Documentation status only. It does not lock editing or change calculation formulas.",
  calculation_type: "Select the active loading method. Highway and Railroad calculations use different API RP 1102 loading tables.",
  scenario_name: "Scenario label used to compare alternate input assumptions within the same calculation.",
  nps: "Nominal pipe size. The outside diameter and wall thickness options update from the standards tables.",
  outside_diameter: "Pipe outside diameter from the selected nominal pipe size.",
  wall_thickness: "Pipe wall thickness used for stress and stiffness calculations.",
  tw_d: "Wall-thickness-to-diameter ratio used for stiffness factor lookup tables.",
  cover_depth: "Depth from ground or track surface to the pipe, in feet.",
  bored_diameter: "Bored or casing opening diameter used for Bd/D and H/Bd lookup factors.",
  bd_d: "Bored-diameter-to-pipe-diameter ratio used for excavation factor lookup.",
  h_bd: "Cover-to-bored-diameter ratio used for burial factor lookup.",
  pipe_specification: "Pipe specification used to determine available grades and SMYS.",
  pipe_grade: "Pipe grade used to determine specified minimum yield strength.",
  smys: "Specified minimum yield strength used for stress allowables.",
  weld_seam_type: "Longitudinal seam type used to determine joint factor and fatigue limits.",
  joint_factor: "Longitudinal joint factor from the selected weld seam type.",
  youngs_modulus: "Elastic modulus used in stress calculations for steel pipe.",
  pipeline_location: "Design-factor category for the pipeline location.",
  class_location: "Class location used with pipeline location to determine design factor F.",
  design_factor: "Design factor F from the standards table.",
  temperature_derating_factor: "Temperature factor applied when operating temperature exceeds the standard threshold.",
  operating_pressure: "Internal operating pressure used for hoop and combined stress checks.",
  installation_temperature: "Temperature at installation used for thermal stress calculation.",
  operating_temperature: "Operating temperature used for temperature derating and thermal stress.",
  soil_type: "Backfill/soil category used to select E' and resilient modulus values.",
  e_prime: "Modulus of soil reaction used for earth-load factors.",
  er: "Resilient modulus used for highway or railroad live-load stiffness factors.",
  soil_unit_weight: "Average unit weight of soil or backfill above the pipe.",
  pavement_type: "Pavement support condition used with axle configuration to select highway load factors.",
  axle_configuration: "Critical highway axle configuration used to select wheel load and load factors.",
  design_wheel_load: "Design wheel load selected from the highway loading table.",
  impact_factor: "Impact factor from API RP 1102 loading tables.",
  track_count: "Number of tracks considered for railroad loading factors.",
  surface_pressure: "Applied railroad surface pressure, typically Cooper E80 equivalent.",
  track_factor: "Double-track correction factors for circumferential and longitudinal stress."
};
const advancedHelp: Record<string, string> = {
  SHi: "Hoop stress from internal pressure using the Barlow relationship.",
  allowable_hoop: "Allowable hoop stress based on SMYS, design factor, joint factor, and temperature factor.",
  SHi_internal: "Internal pressure component used in combined stress calculations.",
  Khe: "Earth-load stiffness factor from API RP 1102 tables.",
  Be: "Burial factor selected from H/Bd and soil modulus table.",
  Ee: "Excavation factor selected from Bd/D lookup table.",
  SHe: "Circumferential stress contribution from earth load.",
  Fi: "Impact factor from the active highway or railroad loading table.",
  KHh: "Highway circumferential stiffness factor.",
  KHr: "Railroad circumferential stiffness factor.",
  GHh: "Highway circumferential geometry factor.",
  GHr: "Railroad circumferential geometry factor.",
  KLh: "Highway longitudinal stiffness factor.",
  KLr: "Railroad longitudinal stiffness factor.",
  SH: "Live-load circumferential stress component.",
  SL: "Live-load longitudinal stress component.",
  SFG: "Calculated girth weld fatigue stress.",
  SFL: "Calculated longitudinal weld fatigue stress.",
  S1: "Maximum circumferential principal stress.",
  S2: "Maximum longitudinal principal stress.",
  S3: "Maximum radial principal stress.",
  Seff: "Total effective stress used for combined stress check.",
  allowable_effective: "Allowable effective stress based on SMYS and design factor.",
  allowable_girth: "Allowable girth weld stress adjusted by design factor.",
  allowable_longitudinal: "Allowable longitudinal weld stress adjusted by design factor."
};

function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [calculations, setCalculations] = useState<Calculation[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeCalc, setActiveCalc] = useState<Calculation | null>(null);
  const [activeScenario, setActiveScenario] = useState<Scenario | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [exportRecords, setExportRecords] = useState<ExportRecord[]>([]);
  const [standards, setStandards] = useState<StandardsPayload | null>(null);
  const [autosave, setAutosave] = useState("Autosaved - just now");

  async function refresh() {
    const [dash, projectList, calcList] = await Promise.all([
      api<DashboardSummary>("/dashboard/summary"),
      api<Project[]>("/projects"),
      api<Calculation[]>("/calculations")
    ]);
    setSummary(dash);
    setProjects(projectList);
    setCalculations(calcList);
    setActiveProject((current) => (current ? projectList.find((project) => project.id === current.id) || current : current));
  }

  async function openProject(project: Project) {
    setActiveProject(project);
    setPage("projectDetail");
  }

  async function openProjectById(id: number) {
    const project = projects.find((item) => item.id === id) || (await api<Project>(`/projects/${id}`));
    await openProject(project);
  }

  async function createProject() {
    const project = await api<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({
        project_name: `New Project ${Math.floor(Math.random() * 9000 + 1000)}`,
        project_number: "",
        client: "",
        location: "",
        description: "",
        status: "Active"
      })
    });
    await refresh();
    await openProject(project);
  }

  async function importProjectPackage(file: File) {
    setAutosave("Importing...");
    try {
      const packageJson = JSON.parse(await file.text());
      const imported = await api<{ project_id: number; project_name: string }>("/exports/import", {
        method: "POST",
        body: JSON.stringify(packageJson)
      });
      await refresh();
      const project = await api<Project>(`/projects/${imported.project_id}`);
      setAutosave("Import complete");
      await openProject(project);
    } catch {
      setAutosave("Import failed");
    }
  }

  async function patchProject(projectId: number, values: Partial<Project>) {
    setAutosave("Saving...");
    try {
      const saved = await api<Project>(`/projects/${projectId}`, { method: "PATCH", body: JSON.stringify(values) });
      setProjects((items) => items.map((project) => (project.id === saved.id ? saved : project)));
      setActiveProject((current) => (current?.id === saved.id ? saved : current));
      setAutosave("Autosaved - just now");
    } catch {
      setAutosave("Save failed");
    }
  }

  async function patchCalculation(calculationId: number, values: Partial<Calculation>) {
    setAutosave("Saving...");
    try {
      const saved = await api<Calculation>(`/calculations/${calculationId}`, { method: "PATCH", body: JSON.stringify(values) });
      setCalculations((items) => items.map((calc) => (calc.id === saved.id ? saved : calc)));
      setActiveCalc((current) => (current?.id === saved.id ? saved : current));
      if (activeCalc?.id === saved.id && values.calculation_type) {
        const scenarioList = await api<Scenario[]>(`/scenarios?calculation_id=${saved.id}`);
        setScenarios(scenarioList);
        setActiveScenario((current) => scenarioList.find((scenario) => scenario.id === current?.id) || scenarioList[0] || null);
      }
      setAutosave("Autosaved - just now");
    } catch {
      setAutosave("Save failed");
    }
  }

  async function duplicateProject(projectId: number) {
    const project = await api<Project>(`/projects/${projectId}/duplicate`, { method: "POST" });
    await refresh();
    await openProject(project);
  }

  async function archiveProject(projectId: number) {
    const project = await api<Project>(`/projects/${projectId}/archive`, { method: "POST" });
    await refresh();
    setActiveProject((current) => (current?.id === projectId ? project : current));
  }

  async function deleteProjects(projectIds: number[]) {
    const uniqueIds = [...new Set(projectIds)];
    if (!uniqueIds.length) return false;
    const message = uniqueIds.length === 1
      ? "Delete this project and all of its calculations? This cannot be undone."
      : `Delete ${uniqueIds.length} selected projects and all of their calculations? This cannot be undone.`;
    if (!window.confirm(message)) {
      return false;
    }
    const activeProjectDeleted = activeProject ? uniqueIds.includes(activeProject.id) : false;
    const activeCalcDeleted = activeCalc ? uniqueIds.includes(activeCalc.project_id) : false;
    for (const projectId of uniqueIds) {
      await api(`/projects/${projectId}`, { method: "DELETE" });
    }
    if (activeProjectDeleted) {
      setActiveProject(null);
      setPage("projects");
    }
    if (activeCalcDeleted) {
      setActiveCalc(null);
      setActiveScenario(null);
      setScenarios([]);
      setExportRecords([]);
    }
    await refresh();
    return true;
  }

  async function deleteProject(projectId: number) {
    return deleteProjects([projectId]);
  }

  async function openCalculation(calc: Calculation) {
    let nextCalc = calc;
    setActiveProject(projects.find((project) => project.id === calc.project_id) || activeProject);
    let [scenarioList, records] = await Promise.all([
      api<Scenario[]>(`/scenarios?calculation_id=${calc.id}`),
      api<ExportRecord[]>(`/exports/records?calculation_id=${calc.id}`)
    ]);
    if (calc.overall_result === "Not Calculated" || scenarioList.some((scenario) => !(scenario.results?.checks || []).length)) {
      await api(`/calculations/${calc.id}/calculate`, { method: "POST" });
      [nextCalc, scenarioList, records] = await Promise.all([
        api<Calculation>(`/calculations/${calc.id}`),
        api<Scenario[]>(`/scenarios?calculation_id=${calc.id}`),
        api<ExportRecord[]>(`/exports/records?calculation_id=${calc.id}`)
      ]);
      setCalculations((items) => items.map((item) => (item.id === nextCalc.id ? nextCalc : item)));
    }
    setActiveCalc(nextCalc);
    setScenarios(scenarioList);
    setActiveScenario(scenarioList[0] || null);
    setExportRecords(records);
    setPage("workspace");
  }

  async function openCalculationById(id: number) {
    await openCalculation(await api<Calculation>(`/calculations/${id}`));
  }

  async function createCalculation(projectId?: number, type: "Highway" | "Railroad" = "Highway") {
    const targetProject = projectId || activeProject?.id || projects[0]?.id;
    if (!targetProject) {
      await createProject();
      return;
    }
    const calc = await api<Calculation>("/calculations", {
      method: "POST",
      body: JSON.stringify({
        project_id: targetProject,
        calc_number: `CALC-${Math.floor(Math.random() * 90000 + 10000)}`,
        crossing_name: "New Crossing",
        calculation_type: type,
        road_highway: type === "Highway" ? "New Highway / Road" : "",
        railroad_route: type === "Railroad" ? "New Railroad / Route" : "",
        status: "Draft"
      })
    });
    await refresh();
    await openCalculation(calc);
  }

  async function duplicateCalculation(calcId: number) {
    const calc = await api<Calculation>(`/calculations/${calcId}/duplicate`, { method: "POST" });
    await refresh();
    await openCalculation(calc);
  }

  async function deleteCalculations(calcIds: number[]) {
    const uniqueIds = [...new Set(calcIds)];
    if (!uniqueIds.length) return false;
    const message = uniqueIds.length === 1
      ? "Delete this calculation and its scenarios? This cannot be undone."
      : `Delete ${uniqueIds.length} selected calculations and their scenarios? This cannot be undone.`;
    if (!window.confirm(message)) {
      return false;
    }
    const activeCalcDeleted = activeCalc ? uniqueIds.includes(activeCalc.id) : false;
    for (const calcId of uniqueIds) {
      await api(`/calculations/${calcId}`, { method: "DELETE" });
    }
    setCalculations((items) => items.filter((item) => !uniqueIds.includes(item.id)));
    if (activeCalcDeleted) {
      setActiveCalc(null);
      setActiveScenario(null);
      setScenarios([]);
      setExportRecords([]);
      setPage("projectDetail");
    }
    await refresh();
    return true;
  }

  async function deleteCalculation(calcId: number) {
    return deleteCalculations([calcId]);
  }

  async function saveScenario(next: Scenario) {
    setAutosave("Saving...");
    try {
      const saved = await api<Scenario>(`/scenarios/${next.id}`, {
        method: "PUT",
        body: JSON.stringify({
          calculation_id: next.calculation_id,
          scenario_name: next.scenario_name,
          description: next.description,
          shared_inputs: next.shared_inputs,
          highway_inputs: next.highway_inputs,
          railroad_inputs: next.railroad_inputs
        })
      });
      setActiveScenario(saved);
      setScenarios((items) => items.map((item) => (item.id === saved.id ? saved : item)));
      const savedCalc = await api<Calculation>(`/calculations/${saved.calculation_id}`);
      setActiveCalc((current) => (current?.id === savedCalc.id ? savedCalc : current));
      setCalculations((items) => items.map((calc) => (calc.id === savedCalc.id ? savedCalc : calc)));
      await refresh();
      setAutosave("Autosaved - just now");
    } catch {
      setAutosave("Save failed");
    }
  }

  async function createScenario(calculationId: number) {
    if (!activeScenario) return;
    const created = await api<Scenario>("/scenarios", {
      method: "POST",
      body: JSON.stringify({
        calculation_id: calculationId,
        scenario_name: `Scenario ${scenarios.length + 1}`,
        description: "",
        shared_inputs: activeScenario.shared_inputs || {},
        highway_inputs: activeScenario.highway_inputs || {},
        railroad_inputs: activeScenario.railroad_inputs || {}
      })
    });
    const savedCalc = await api<Calculation>(`/calculations/${calculationId}`);
    setActiveCalc((current) => (current?.id === savedCalc.id ? savedCalc : current));
    setCalculations((items) => items.map((calc) => (calc.id === savedCalc.id ? savedCalc : calc)));
    setScenarios((items) => [...items, created]);
    setActiveScenario(created);
  }

  async function duplicateScenario(scenarioId: number) {
    const created = await api<Scenario>(`/scenarios/${scenarioId}/duplicate`, { method: "POST" });
    const savedCalc = await api<Calculation>(`/calculations/${created.calculation_id}`);
    setActiveCalc((current) => (current?.id === savedCalc.id ? savedCalc : current));
    setCalculations((items) => items.map((calc) => (calc.id === savedCalc.id ? savedCalc : calc)));
    setScenarios((items) => [...items, created]);
    setActiveScenario(created);
  }

  async function deleteScenario(scenarioId: number) {
    if (scenarios.length <= 1) return;
    await api(`/scenarios/${scenarioId}`, { method: "DELETE" });
    const remaining = scenarios.filter((scenario) => scenario.id !== scenarioId);
    if (activeCalc) {
      const savedCalc = await api<Calculation>(`/calculations/${activeCalc.id}`);
      setActiveCalc(savedCalc);
      setCalculations((items) => items.map((calc) => (calc.id === savedCalc.id ? savedCalc : calc)));
    }
    setScenarios(remaining);
    setActiveScenario(remaining[0] || null);
  }

  useEffect(() => {
    refresh().catch(console.error);
    api<StandardsPayload>("/standards/tables").then(setStandards).catch(console.error);
  }, []);

  return (
    <AppShell page={page} setPage={setPage} autosave={autosave} activeCalc={activeCalc}>
      {page === "dashboard" ? (
        <Dashboard
          summary={summary}
          projects={projects}
          calculations={calculations}
          onOpenProject={openProject}
          onOpenCalculationId={openCalculationById}
          onNewProject={createProject}
          onImportProject={importProjectPackage}
          onNewCalculation={() => createCalculation(activeProject?.id)}
        />
      ) : null}
      {page === "projects" ? (
        <ProjectsPage
          projects={projects}
          calculations={calculations}
          onOpen={openProject}
          onNewProject={createProject}
          onImportProject={importProjectPackage}
          onDuplicate={duplicateProject}
          onArchive={archiveProject}
          onDelete={deleteProject}
          onDeleteSelected={deleteProjects}
        />
      ) : null}
      {page === "projectDetail" && activeProject ? (
        <ProjectDetail
          project={activeProject}
          calculations={calculations.filter((calc) => calc.project_id === activeProject.id)}
          onBack={() => setPage("projects")}
          onOpenCalculation={openCalculation}
          onNewCalculation={(type) => createCalculation(activeProject.id, type)}
          onDuplicateProject={() => duplicateProject(activeProject.id)}
          onDeleteProject={() => deleteProject(activeProject.id)}
          onDeleteCalculation={deleteCalculation}
          onDeleteCalculations={deleteCalculations}
          onPatchProject={(values) => patchProject(activeProject.id, values)}
          onImportProject={importProjectPackage}
        />
      ) : null}
      {page === "workspace" && activeCalc && activeScenario ? (
        <CalculationWorksheet
          project={projects.find((item) => item.id === activeCalc.project_id) || activeProject}
          calc={activeCalc}
          scenario={activeScenario}
          scenarios={scenarios}
          exportRecords={exportRecords}
          standards={standards}
          setScenario={setActiveScenario}
          saveScenario={saveScenario}
          patchCalculation={patchCalculation}
          onCreateScenario={() => createScenario(activeCalc.id)}
          onDuplicateScenario={() => duplicateScenario(activeScenario.id)}
          onDeleteScenario={() => deleteScenario(activeScenario.id)}
          onSelectScenario={setActiveScenario}
          onBack={() => openProjectById(activeCalc.project_id)}
          onDuplicate={() => duplicateCalculation(activeCalc.id)}
          onReport={() => setPage("report")}
        />
      ) : null}
      {page === "report" && activeCalc && activeScenario ? (
        <ReportPreview calc={activeCalc} project={projects.find((item) => item.id === activeCalc.project_id) || activeProject} scenario={activeScenario} onBack={() => setPage("workspace")} />
      ) : null}
      {page === "standards" ? <Standards /> : null}
      {page === "references" ? <References /> : null}
      {page === "about" ? <About /> : null}
    </AppShell>
  );
}

function Dashboard({
  summary,
  projects,
  calculations,
  onOpenProject,
  onOpenCalculationId,
  onNewProject,
  onImportProject,
  onNewCalculation
}: {
  summary: DashboardSummary | null;
  projects: Project[];
  calculations: Calculation[];
  onOpenProject: (project: Project) => void;
  onOpenCalculationId: (id: number) => void;
  onNewProject: () => void;
  onImportProject: (file: File) => void;
  onNewCalculation: () => void;
}) {
  const [filter, setFilter] = useState("");
  const rows = useMemo(() => {
    return (summary?.recent || []).filter((row) => {
      const matchesSearch = JSON.stringify(row).toLowerCase().includes(filter.toLowerCase());
      return matchesSearch;
    });
  }, [summary, filter]);
  const passRate = summary && summary.total_calculations ? `${Math.round((summary.passing_calculations / summary.total_calculations) * 100)}%` : "0%";

  return (
    <div className="screen-stack">
      <PageTitle
        title="Engineering Dashboard"
        subtitle="API RP 1102 loading analysis for gas pipeline highway and railroad crossings."
        action={<ImportProjectButton onImport={onImportProject} />}
      />

      <Panel className="tip-panel">
        <span>
          <strong>Tip:</strong> This app uses portable project files for storage. An example project is loaded by default so you can explore the tool.
          When you finish a work session, open any project and use <em>Export Project</em> to save a <code>.hdr1102.json</code> file.
          Re-import the file next session from the Dashboard or Projects page to pick up exactly where you left off.
        </span>
      </Panel>

      <div className="metric-grid">
        <MetricCard icon={<FolderPlus size={18} />} label="Projects" value={summary?.total_projects ?? 0} />
        <MetricCard icon={<Calculator size={18} />} label="Calculations" value={summary?.total_calculations ?? 0} />
        <MetricCard icon={<ShieldCheck size={18} />} label="Pass Rate" value={passRate} />
        <MetricCard icon={<AlertTriangle size={18} />} label="In Review" value={summary?.by_status?.["For Review"] ?? 0} />
      </div>

      <Panel className="table-panel">
        <div className="table-toolbar">
          <SearchBox value={filter} onChange={setFilter} placeholder="Search project, crossing, calc number, engineer..." />
          <Button icon={<Plus size={17} />} onClick={onNewProject}>
            New Project
          </Button>
          <Button variant="primary" icon={<Plus size={17} />} onClick={onNewCalculation}>
            New Calculation
          </Button>
        </div>
        <CalculationTable rows={rows} onOpenId={onOpenCalculationId} />
      </Panel>

      <Panel>
        <SectionHeader title="Recent Projects" subtitle="Open a project to manage its calculations." />
        <div className="project-card-grid">
          {recentProjects(projects, calculations).map((project) => (
            <button className="project-card clickable" key={project.id} onClick={() => onOpenProject(project)}>
              <span>{project.project_number || `Project ID ${project.id}`}</span>
              <strong>{project.project_name || "Untitled Project"}</strong>
              <small>{project.client || "No client"} / {projectCalcCount(project.id, calculations)} calculations</small>
            </button>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function CalculationTable({ rows, onOpenId }: { rows: DashboardSummary["recent"]; onOpenId: (id: number) => void }) {
  return (
    <div className="table-scroll">
      <table className="engineering-table">
        <thead>
          <tr>
            <th>Calc #</th>
            <th>Project</th>
            <th>Crossing</th>
            <th>Pipe Size</th>
            <th>Result</th>
            <th>Modified</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} onClick={() => onOpenId(row.id)}>
              <td>{row.calc_number}</td>
              <td>{row.project}</td>
              <td>{row.crossing_name}</td>
              <td>{row.pipe_size}</td>
              <td><ResultBadge value={row.result} /></td>
              <td>{formatDate(row.modified_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProjectsPage({
  projects,
  calculations,
  onOpen,
  onNewProject,
  onImportProject,
  onDuplicate,
  onArchive,
  onDelete,
  onDeleteSelected
}: {
  projects: Project[];
  calculations: Calculation[];
  onOpen: (project: Project) => void;
  onNewProject: () => void;
  onImportProject: (file: File) => void;
  onDuplicate: (id: number) => void;
  onArchive: (id: number) => void;
  onDelete: (id: number) => Promise<boolean> | boolean;
  onDeleteSelected: (ids: number[]) => Promise<boolean> | boolean;
}) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const visible = projects.filter((project) => JSON.stringify(project).toLowerCase().includes(query.toLowerCase()));
  const selectedText = `${selected.length} selected`;

  function toggle(projectId: number) {
    setSelected((items) => (items.includes(projectId) ? items.filter((id) => id !== projectId) : [...items, projectId]));
  }

  function exportSelected() {
    selected.forEach((projectId) => window.open(`/api/exports/project/${projectId}.json`, "_blank"));
  }

  async function deleteSelected() {
    const deleted = await onDeleteSelected(selected);
    if (deleted) setSelected([]);
  }

  return (
    <div className="screen-stack">
      <div className="projects-heading">
        <h1><FolderOpen size={27} /> Projects</h1>
        <p>Organize crossings, calculations, and revisions by project. Export a project (or a bundle of projects) to save your work; import it later to resume.</p>
      </div>
      <div className="project-actions">
        <ImportProjectButton onImport={onImportProject} />
        <Button variant="primary" icon={<Plus size={17} />} onClick={onNewProject}>New Project</Button>
      </div>
      <Panel className="table-panel">
        <div className="projects-action-bar">
          <SearchBox value={query} onChange={setQuery} placeholder="Search projects..." />
          <span>{selectedText}</span>
          <Button href={selected.length === 1 ? `/api/exports/project/${selected[0]}.json` : undefined} onClick={selected.length > 1 ? exportSelected : undefined} icon={<Download size={16} />}>Export Selected</Button>
          {selected.length ? <Button icon={<Trash2 size={16} />} onClick={deleteSelected}>Delete Selected</Button> : null}
        </div>
        <div className="table-scroll">
          <table className="engineering-table project-table">
            <thead>
              <tr>
                <th><input type="checkbox" checked={visible.length > 0 && selected.length === visible.length} onChange={() => setSelected(selected.length === visible.length ? [] : visible.map((project) => project.id))} /></th>
                <th>Project</th>
                <th>Number</th>
                <th>Client</th>
                <th>Location</th>
                <th>Calculations</th>
                <th>Modified</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((project) => (
                <tr key={project.id} onClick={() => onOpen(project)}>
                  <td onClick={(event) => event.stopPropagation()}><input type="checkbox" checked={selected.includes(project.id)} onChange={() => toggle(project.id)} /></td>
                  <td><strong>{project.project_name || "Untitled Project"}</strong></td>
                  <td>{project.project_number || "-"}</td>
                  <td>{project.client || "-"}</td>
                  <td>{project.location || "-"}</td>
                  <td>{projectCalcCount(project.id, calculations)}</td>
                  <td>{formatDate(project.updated_at || project.created_at || "")}</td>
                  <td onClick={(event) => event.stopPropagation()}>
                    <div className="icon-actions">
                      <button title="Duplicate" onClick={() => onDuplicate(project.id)}><Copy size={16} /></button>
                      <button title="Delete" className="danger" onClick={() => onDelete(project.id)}><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function ProjectDetail({
  project,
  calculations,
  onBack,
  onOpenCalculation,
  onNewCalculation,
  onDuplicateProject,
  onDeleteProject,
  onDeleteCalculation,
  onDeleteCalculations,
  onPatchProject,
  onImportProject
}: {
  project: Project;
  calculations: Calculation[];
  onBack: () => void;
  onOpenCalculation: (calc: Calculation) => void;
  onNewCalculation: (type: "Highway" | "Railroad") => void;
  onDuplicateProject: () => void;
  onDeleteProject: () => void;
  onDeleteCalculation: (calculationId: number) => Promise<boolean> | boolean;
  onDeleteCalculations: (calculationIds: number[]) => Promise<boolean> | boolean;
  onPatchProject: (values: Partial<Project>) => void;
  onImportProject: (file: File) => void;
}) {
  const [selectedCalcIds, setSelectedCalcIds] = useState<number[]>([]);
  const allCalculationsSelected = calculations.length > 0 && selectedCalcIds.length === calculations.length;

  useEffect(() => {
    setSelectedCalcIds((ids) => {
      const visibleIds = new Set(calculations.map((calc) => calc.id));
      const next = ids.filter((id) => visibleIds.has(id));
      return next.length === ids.length ? ids : next;
    });
  }, [project.id, calculations]);

  function toggleCalculation(calculationId: number) {
    setSelectedCalcIds((ids) => (ids.includes(calculationId) ? ids.filter((id) => id !== calculationId) : [...ids, calculationId]));
  }

  async function deleteSelectedCalculations() {
    const deleted = await onDeleteCalculations(selectedCalcIds);
    if (deleted) setSelectedCalcIds([]);
  }

  return (
    <div className="screen-stack">
      <div className="project-detail-header">
        <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to Projects</button>
        <div>
          <h1>{project.project_name || "Untitled Project"}</h1>
          <p>{project.project_number || "No project number"} / {project.client || "No client"} / {project.location || "No location"}</p>
        </div>
        <div className="inline-actions">
          <Button icon={<Copy size={16} />} onClick={onDuplicateProject}>Duplicate Project</Button>
          <Button icon={<Trash2 size={16} />} onClick={onDeleteProject}>Delete Project</Button>
          <ImportProjectButton onImport={onImportProject} compact />
          <Button variant="primary" href={`/api/exports/project/${project.id}.json`} icon={<Download size={16} />}>Export Project</Button>
        </div>
      </div>
      <Panel>
        <SectionHeader title="Project Information" right={<StatusPill value={project.status || "Active"} />} />
        <div className="form-grid three">
          <Field label="Project Name" value={project.project_name || ""} onChange={(value) => onPatchProject({ project_name: value })} helpText={fieldHelp.project_name} />
          <Field label="Project Number" value={project.project_number || ""} onChange={(value) => onPatchProject({ project_number: value })} helpText={fieldHelp.project_number} />
          <Field label="Client" value={project.client || ""} onChange={(value) => onPatchProject({ client: value })} helpText={fieldHelp.client} />
          <Field label="Location" value={project.location || ""} onChange={(value) => onPatchProject({ location: value })} helpText={fieldHelp.location} />
          <Field label="Status" value={project.status || "Active"} select options={projectStatuses} onChange={(value) => onPatchProject({ status: value })} helpText="Project organization status only. It does not affect calculations." />
          <Field label="Modified Date" value={formatDate(project.updated_at || project.created_at || "")} readOnly helpText="Last saved date for this project record." />
        </div>
        <p className="detail-description">{project.description || "No project description has been entered."}</p>
      </Panel>
      <Panel>
        <SectionHeader
          title="Calculations"
          subtitle="Every calculation belongs to this project."
          right={
            <div className="inline-actions">
              <Button icon={<Car size={16} />} onClick={() => onNewCalculation("Highway")}>New Highway Calc</Button>
              <Button variant="primary" icon={<RailSymbol size={16} />} onClick={() => onNewCalculation("Railroad")}>New Railroad Calc</Button>
            </div>
          }
        />
        {calculations.length ? (
          <>
            <div className="calc-selection-bar">
              <span>{selectedCalcIds.length} selected</span>
              {selectedCalcIds.length ? <Button icon={<Trash2 size={16} />} onClick={deleteSelectedCalculations}>Delete Selected Calculations</Button> : null}
            </div>
            <div className="table-scroll">
              <table className="engineering-table project-calcs-table">
                <thead><tr><th><input type="checkbox" checked={allCalculationsSelected} onChange={() => setSelectedCalcIds(allCalculationsSelected ? [] : calculations.map((calc) => calc.id))} /></th><th>Calc #</th><th>Crossing</th><th>Type</th><th>Status</th><th>Result</th><th>Controlling Check</th><th>Revision</th><th>Actions</th></tr></thead>
                <tbody>
                  {calculations.map((calc) => (
                    <tr key={calc.id} onClick={() => onOpenCalculation(calc)}>
                      <td onClick={(event) => event.stopPropagation()}><input type="checkbox" checked={selectedCalcIds.includes(calc.id)} onChange={() => toggleCalculation(calc.id)} /></td>
                      <td>{calc.calc_number}</td>
                      <td>{calc.crossing_name}</td>
                      <td>{calc.calculation_type}</td>
                      <td><StatusPill value={calc.status} /></td>
                      <td><ResultBadge value={calc.overall_result} /></td>
                      <td>{calc.controlling_check || "-"}</td>
                      <td>{calc.revision || "0"}</td>
                      <td onClick={(event) => event.stopPropagation()}>
                        <div className="icon-actions">
                          <button title="Delete Calculation" className="danger" onClick={() => onDeleteCalculation(calc.id)}><Trash2 size={16} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="empty-calcs">
            <Calculator size={32} />
            <strong>No calculations yet</strong>
            <span>Create a highway or railroad calculation to begin documenting this project crossing.</span>
          </div>
        )}
      </Panel>
    </div>
  );
}

function CalculationWorksheet({
  project,
  calc,
  scenario,
  scenarios,
  exportRecords,
  standards,
  setScenario,
  saveScenario,
  patchCalculation,
  onCreateScenario,
  onDuplicateScenario,
  onDeleteScenario,
  onSelectScenario,
  onBack,
  onDuplicate,
  onReport
}: {
  project: Project | null;
  calc: Calculation;
  scenario: Scenario;
  scenarios: Scenario[];
  exportRecords: ExportRecord[];
  standards: StandardsPayload | null;
  setScenario: (scenario: Scenario) => void;
  saveScenario: (scenario: Scenario) => void;
  patchCalculation: (calculationId: number, values: Partial<Calculation>) => void;
  onCreateScenario: () => void;
  onDuplicateScenario: () => void;
  onDeleteScenario: () => void;
  onSelectScenario: (scenario: Scenario) => void;
  onBack: () => void;
  onDuplicate: () => void;
  onReport: () => void;
}) {
  const [loadingTab, setLoadingTab] = useState<LoadingMode>(calc.calculation_type === "Railroad" ? "railroad" : "highway");

  useEffect(() => {
    setLoadingTab(calc.calculation_type === "Railroad" ? "railroad" : "highway");
  }, [calc.id, calc.calculation_type]);

  function patch(part: "shared_inputs" | "highway_inputs" | "railroad_inputs", key: string, value: any) {
    patchMany(part, { [key]: value });
  }

  function patchMany(part: "shared_inputs" | "highway_inputs" | "railroad_inputs", values: Record<string, any>) {
    const next = { ...scenario, [part]: { ...(scenario as any)[part], ...values } };
    setScenario(next);
    window.clearTimeout((window as any).__saveTimer);
    (window as any).__saveTimer = window.setTimeout(() => saveScenario(next), 500);
  }

  return (
    <div className="screen-stack worksheet-stack">
      <div className="calc-hero">
        <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back</button>
        <div>
          <h1>{calc.calc_number} - {calc.crossing_name}</h1>
          <p>{project?.project_name || `Project ${calc.project_id}`} / {calc.road_highway || calc.railroad_route || "Crossing route not entered"}</p>
        </div>
        <div className="calc-header-badges">
          <StatusPill value={calc.status || "Draft"} />
          <ResultBadge value={calc.overall_result || "Not Calculated"} />
          <span className="calc-type-chip">{calc.calculation_type}</span>
          <Button icon={<Copy size={16} />} onClick={onDuplicate}>Duplicate Calc</Button>
          <Button variant="primary" icon={<FileText size={16} />} onClick={onReport}>Report</Button>
        </div>
      </div>

      <MetadataPanel calc={calc} project={project} onPatch={(values) => patchCalculation(calc.id, values)} />
      <ScenarioBar scenario={scenario} scenarios={scenarios} onSelect={onSelectScenario} onCreate={onCreateScenario} onDuplicate={onDuplicateScenario} onDelete={onDeleteScenario} onRename={(scenarioName) => saveScenario({ ...scenario, scenario_name: scenarioName })} />
      <div className="loading-tabs">
        <button className={loadingTab === "highway" ? "active" : ""} onClick={() => setLoadingTab("highway")}>
          <Car size={18} /> Highway Loading <span>{loadingTab === "highway" ? "Active" : ""}</span>
        </button>
        <button className={loadingTab === "railroad" ? "active" : ""} onClick={() => setLoadingTab("railroad")}>
          <RailSymbol size={18} /> Railroad Loading <span>{loadingTab === "railroad" ? "Active" : ""}</span>
        </button>
      </div>
      <div className="loading-note">
        {loadingTab === "railroad"
          ? "Railroad loading per API RP 1102 §4. Shared inputs (pipe, soil, pressure, temperature) persist between tabs."
          : "Highway loading per API RP 1102 §3 (Figures 14-17). Shared inputs (pipe, soil, pressure, temperature) persist between tabs."}
      </div>
      <LoadingForm mode={loadingTab} scenario={scenario} standards={standards} patch={patch} patchMany={patchMany} />
      <ResultsPanel result={scenario.results} warnings={scenario.warnings} />
      <AdvancedPanel result={scenario.results} intermediate={scenario.intermediate_values} warnings={scenario.warnings} />
      <ExportHistory records={exportRecords} calc={calc} scenario={scenario} />
    </div>
  );
}

function MetadataPanel({ calc, project, onPatch }: { calc: Calculation; project?: Project | null; onPatch?: (values: Partial<Calculation>) => void }) {
  function guardedPatch(values: Partial<Calculation>) {
    onPatch?.(values);
  }

  return (
    <Panel className="metadata-panel">
      <SectionHeader title="Calculation Metadata" subtitle="Documentation fields only. Status does not lock or route the calculation." />
      <div className="metadata-grid">
        <Field label="Project Name" value={project?.project_name || `Project ${calc.project_id}`} readOnly helpText={fieldHelp.project_name} />
        <Field label="Project Number" value={project?.project_number || ""} readOnly helpText={fieldHelp.project_number} />
        <Field label="Client" value={project?.client || ""} readOnly helpText={fieldHelp.client} />
        <Field label="Location" value={project?.location || ""} readOnly helpText={fieldHelp.location} />
        <Field label="Calc Number" value={calc.calc_number} onChange={(value) => guardedPatch({ calc_number: value })} helpText={fieldHelp.calc_number} />
        <Field label="Crossing Name" value={calc.crossing_name} onChange={(value) => guardedPatch({ crossing_name: value })} helpText={fieldHelp.crossing_name} />
        <Field label="Road / Highway" value={calc.road_highway || ""} onChange={(value) => guardedPatch({ road_highway: value })} helpText={fieldHelp.route} />
        <Field label="Revision" value={calc.revision || "0"} onChange={(value) => guardedPatch({ revision: value })} helpText={fieldHelp.revision} />
        <Field label="Prepared By" value={calc.prepared_by || ""} onChange={(value) => guardedPatch({ prepared_by: value })} helpText="Engineer or preparer responsible for the calculation." />
        <Field label="Checked By" value={calc.checked_by || ""} onChange={(value) => guardedPatch({ checked_by: value })} helpText="Independent checker or reviewer name for documentation." />
        <Field label="Reviewer" value={calc.reviewer || ""} onChange={(value) => guardedPatch({ reviewer: value })} helpText="Optional additional reviewer for client or internal review." />
        <Field label="Date" value={calc.date || ""} onChange={(value) => guardedPatch({ date: value || null })} helpText="Calculation date shown in reports and exports." />
        <Field label="Status" value={calc.status || "Draft"} select options={statusOptions} onChange={(value) => guardedPatch({ status: value })} helpText={fieldHelp.status} />
        <Field label="Calculation Type" value={calc.calculation_type} select options={["Highway", "Railroad"]} onChange={(value) => guardedPatch({ calculation_type: value })} helpText={fieldHelp.calculation_type} />
        <Field label="Railroad / Route" value={calc.railroad_route || ""} onChange={(value) => guardedPatch({ railroad_route: value })} helpText={fieldHelp.route} />
        <Field label="Review Comments" value={calc.review_comments || ""} onChange={(value) => guardedPatch({ review_comments: value })} helpText="Short documentation note for review comments or disposition." />
        <div className="wide">
          <Field label="Notes" value={calc.notes || ""} onChange={(value) => guardedPatch({ notes: value })} textarea helpText="Assumptions, limitations, or project-specific notes included in the calculation package." />
        </div>
      </div>
    </Panel>
  );
}

function ScenarioBar({
  scenario,
  scenarios,
  onSelect,
  onCreate,
  onDuplicate,
  onDelete,
  onRename
}: {
  scenario: Scenario;
  scenarios: Scenario[];
  onSelect: (scenario: Scenario) => void;
  onCreate: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onRename: (value: string) => void;
}) {
  return (
    <Panel className="scenario-panel">
      <div className="scenario-row">
        <span>Scenario:</span>
        {scenarios.map((item) => (
          <button key={item.id} className={`scenario-pill ${item.id === scenario.id ? "active" : ""}`} onClick={() => onSelect(item)}>
            {item.scenario_name || "Base Case"}
          </button>
        ))}
        <Button icon={<Plus size={16} />} onClick={onCreate}>Add Scenario</Button>
        <Button icon={<Copy size={16} />} onClick={onDuplicate}>Duplicate</Button>
        <Button icon={<Trash2 size={16} />} onClick={onDelete}>Delete</Button>
      </div>
      <Field label="Scenario Name" value={scenario.scenario_name || "Base Case"} onChange={onRename} helpText={fieldHelp.scenario_name} />
    </Panel>
  );
}

function LoadingForm({
  mode,
  scenario,
  standards,
  patch,
  patchMany
}: {
  mode: LoadingMode;
  scenario: Scenario;
  standards: StandardsPayload | null;
  patch: (part: "shared_inputs" | "highway_inputs" | "railroad_inputs", key: string, value: any) => void;
  patchMany: (part: "shared_inputs" | "highway_inputs" | "railroad_inputs", values: Record<string, any>) => void;
}) {
  const shared = scenario.shared_inputs || {};
  const resultValues = firstIntermediate(scenario.intermediate_values);
  const highway = scenario.highway_inputs || {};
  const railroad = scenario.railroad_inputs || {};
  const isRail = mode === "railroad";
  const pipeDimensions = standards?.pipe_dimensions || {};
  const pipeGrades = standards?.pipe_grades || {};
  const dropdowns = standards?.dropdown_options || {};
  const selectedNps = String(shared.nps || "12");
  const npsOptions = keys(pipeDimensions, ["8", "10", "12", "16"]);
  const pipeInfo = pipeDimensions[selectedNps] || pipeDimensions["12"] || {};
  const wallOptions = pipeInfo.wall_thickness_options || [0.18, 0.203, 0.219, 0.25, 0.281, 0.312, 0.33, 0.344, 0.375, 0.406, 0.438, 0.5];
  const wallThicknessValue = shared.wall_thickness ?? 0.25;
  const wallThicknessNumber = Number(wallThicknessValue);
  const wallThicknessIsNonstandard =
    Number.isFinite(wallThicknessNumber) &&
    wallThicknessNumber > 0 &&
    !wallOptions.some((option: number) => Math.abs(Number(option) - wallThicknessNumber) < 1e-9);
  const specificationOptions = keys(pipeGrades, dropdowns.pipe_specifications || ["API 5L"]);
  const selectedSpec = String(shared.pipe_specification || "API 5L");
  const gradeOptions = keys(pipeGrades[selectedSpec], ["X42", "X52", "X65"]);
  const weldOptions = keys(standards?.weld_seam_factors, ["Electric Resistance Welded"]);
  const pipelineOptions = keys(standards?.design_factors, dropdowns.pipeline_locations || ["Pipelines, mains, and service lines"]);
  const classOptions = dropdowns.class_locations || ["1", "2", "3", "4"];
  const soilOptions = keys(standards?.soil_properties, dropdowns.soil_types || ["Loose sands and gravels"]);
  const pavementOptions = dropdowns.pavement_types || ["Flexible", "Rigid"];
  const axleOptions = dropdowns.axle_configurations || ["Single Axle", "Tandem Axle"];
  const trackOptions = dropdowns.track_counts || [1, 2];
  const displayedOd = resultValues.nps === selectedNps ? resultValues.outside_diameter : pipeInfo.outside_diameter || resultValues.outside_diameter || 12.75;

  return (
    <div className="loading-layout">
      <div className="form-column">
        <Panel>
          <SectionHeader title="A. Pipeline Geometry" />
          <div className="form-grid two">
            <Field label="Nominal Pipe Diameter (NPS)" value={selectedNps} onChange={(v) => patchMany("shared_inputs", nextPipeSelection(v, shared.wall_thickness, shared.bored_diameter, pipeDimensions))} select options={npsOptions} helpText={fieldHelp.nps} />
            <Field label="Pipe Outside Diameter, D (in)" value={fmt(displayedOd, 4)} readOnly helpText={fieldHelp.outside_diameter} />
            <Field
              label="Wall Thickness tw (in)"
              value={wallThicknessValue}
              onChange={(v) => patch("shared_inputs", "wall_thickness", numeric(v))}
              freeformOptions
              options={wallOptions}
              hint={wallThicknessIsNonstandard ? "Nonstandard value - calculation uses this custom thickness." : undefined}
              helpText={fieldHelp.wall_thickness}
            />
            <Field label="tw / D (Auto)" value={fmt(resultValues.tw_d || 0.0294, 4)} readOnly helpText={fieldHelp.tw_d} />
            <Field label="Pipe Depth / Cover H (ft)" value={shared.cover_depth ?? 6} onChange={(v) => patch("shared_inputs", "cover_depth", numeric(v))} hint="Recommended 3-10 ft (allowable 1-30 ft)" helpText={fieldHelp.cover_depth} />
            <Field label="Bored Diameter Bd (in)" value={shared.bored_diameter ?? 14.75} onChange={(v) => patch("shared_inputs", "bored_diameter", numeric(v))} hint="Typical: D + 2 in new" helpText={fieldHelp.bored_diameter} />
            <Field label="Bd / D (Auto)" value={fmt(resultValues.bd_d || 1.1569, 4)} readOnly helpText={fieldHelp.bd_d} />
            <Field label="H / Bd (Auto)" value={fmt(resultValues.h_bd || 4.8814, 4)} readOnly helpText={fieldHelp.h_bd} />
          </div>
        </Panel>
        <Schematic mode={mode} values={resultValues} />
        <Panel>
          <SectionHeader title="B. Pipe Material" />
          <div className="form-grid two">
            <Field label="Pipe Specification" value={selectedSpec} onChange={(v) => patchMany("shared_inputs", nextSpecificationSelection(v, shared.pipe_grade, pipeGrades))} select options={specificationOptions} helpText={fieldHelp.pipe_specification} />
            <Field label="Pipe Grade" value={shared.pipe_grade || (isRail ? "X42" : "X65")} onChange={(v) => patch("shared_inputs", "pipe_grade", v)} select options={gradeOptions} helpText={fieldHelp.pipe_grade} />
            <Field label="SMYS" value={fmt(resultValues.smys || (isRail ? 42000 : 65000))} readOnly unit="psi" helpText={fieldHelp.smys} />
            <Field label="Weld Seam Type" value={shared.weld_seam_type || "Electric Resistance Welded"} onChange={(v) => patch("shared_inputs", "weld_seam_type", v)} select options={weldOptions} helpText={fieldHelp.weld_seam_type} />
            <Field label="Longitudinal Joint Factor E" value={fmt(resultValues.joint_factor || 1, 3)} readOnly helpText={fieldHelp.joint_factor} />
            <Field label="Young's Modulus Es" value={fmt(resultValues.youngs_modulus || 29000000)} readOnly unit="psi" helpText={fieldHelp.youngs_modulus} />
          </div>
        </Panel>
        <Panel>
          <SectionHeader title="C. Design / Location" />
          <div className="form-grid two">
            <Field label="Pipeline Location" value={shared.pipeline_location || "Pipelines, mains, and service lines"} onChange={(v) => patch("shared_inputs", "pipeline_location", v)} select options={pipelineOptions} helpText={fieldHelp.pipeline_location} />
            <Field label="Class Location" value={shared.class_location || "1"} onChange={(v) => patch("shared_inputs", "class_location", v)} select options={classOptions} helpText={fieldHelp.class_location} />
            <Field label="Design Factor F" value={fmt(resultValues.design_factor || 0.72, 3)} readOnly helpText={fieldHelp.design_factor} />
            <Field label="Temperature Derating Factor T" value={fmt(resultValues.temperature_derating_factor || 1, 3)} readOnly helpText={fieldHelp.temperature_derating_factor} />
          </div>
        </Panel>
        <Panel>
          <SectionHeader title="D. Operating Conditions" />
          <div className="form-grid two">
            <Field label="Operating Pressure P" value={shared.operating_pressure ?? (isRail ? 800 : 1000)} onChange={(v) => patch("shared_inputs", "operating_pressure", numeric(v))} unit="psi" helpText={fieldHelp.operating_pressure} />
            <Field label="Installation Temperature T1" value={shared.installation_temperature ?? 70} onChange={(v) => patch("shared_inputs", "installation_temperature", numeric(v))} unit="F" helpText={fieldHelp.installation_temperature} />
            <Field label="Operating Temperature T2" value={shared.operating_temperature ?? 70} onChange={(v) => patch("shared_inputs", "operating_temperature", numeric(v))} unit="F" helpText={fieldHelp.operating_temperature} />
          </div>
        </Panel>
        <Panel>
          <SectionHeader title="E. Soil / Backfill" />
          <div className="form-grid two">
            <Field label="Soil Type" value={shared.soil_type || (isRail ? "Soft to medium clays and silts with high plasticities" : "Loose sands and gravels")} onChange={(v) => patch("shared_inputs", "soil_type", v)} select options={soilOptions} helpText={fieldHelp.soil_type} />
            <Field label="E' Modulus of Soil Reaction" value={fmt(resultValues.e_prime || (isRail ? 200 : 500))} readOnly unit="psi" helpText={fieldHelp.e_prime} />
            <Field label="Er Resilient Modulus" value={fmt(resultValues.er || (isRail ? 5000 : 10000))} readOnly unit="psi" helpText={fieldHelp.er} />
            <Field label="Average Unit Weight of Soil" value={shared.soil_unit_weight ?? 120} onChange={(v) => patch("shared_inputs", "soil_unit_weight", numeric(v))} unit="pcf" helpText={fieldHelp.soil_unit_weight} />
          </div>
        </Panel>
        <Panel>
          <SectionHeader title={isRail ? "F. Railroad Loading" : "F. Highway Loading"} />
          <div className="form-grid two">
            {isRail ? (
              <>
                <Field label="Number of Tracks" value={railroad.number_of_tracks || 2} onChange={(v) => patch("railroad_inputs", "number_of_tracks", numeric(v))} select options={trackOptions} helpText={fieldHelp.track_count} />
                <Field label="Applied Design Surface Pressure w (psi)" value={railroad.surface_pressure || 13.9} onChange={(v) => patch("railroad_inputs", "surface_pressure", numeric(v))} hint="Default 13.9 psi per API 1102 / Cooper E80" helpText={fieldHelp.surface_pressure} />
                <Field label="Impact Factor Fi (Auto, Railroad Curve)" value={fmt(resultValues.Fi || 1.726, 4)} readOnly helpText={fieldHelp.impact_factor} />
                <Field label="Track Factor (NH / NL Auto)" value={`${fmt(resultValues.Nh || 1, 3)} / ${fmt(resultValues.NL || 1, 3)}`} readOnly helpText={fieldHelp.track_factor} />
              </>
            ) : (
              <>
                <Field label="Pavement Type" value={highway.pavement_type || "Flexible"} onChange={(v) => patch("highway_inputs", "pavement_type", v)} select options={pavementOptions} helpText={fieldHelp.pavement_type} />
                <Field label="Critical Axle Configuration" value={highway.axle_configuration || "Tandem Axle"} onChange={(v) => patch("highway_inputs", "axle_configuration", v)} select options={axleOptions} helpText={fieldHelp.axle_configuration} />
                <Field label="Design Wheel Load W" value={fmt(resultValues.design_wheel_load || 10000)} readOnly unit="lb" helpText={fieldHelp.design_wheel_load} />
                <Field label="Impact Factor Fi" value={fmt(resultValues.Fi || 1.476, 4)} readOnly helpText={fieldHelp.impact_factor} />
              </>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Schematic({ mode, values }: { mode: LoadingMode; values: Record<string, any> }) {
  return (
    <Panel className="schematic-panel">
      <SectionHeader title="Cross-Section Schematic" subtitle="Live diagram derived from current inputs." />
      <CrossSectionDiagram mode={mode} values={values} />
    </Panel>
  );
}

function CrossSectionDiagram({ mode, values, compact = false }: { mode: LoadingMode; values: Record<string, any>; compact?: boolean }) {
  const cover = Math.max(Number(values.cover_depth || 6), 0.1);
  const d = Math.max(Number(values.outside_diameter || 12.75), 0.1);
  const bd = Math.max(Number(values.bored_diameter || 14.75), d);
  const tw = Math.max(Number(values.wall_thickness || 0.25), 0.01);
  const loadLabel = mode === "railroad" ? `w = ${fmt(values.surface_pressure || 13.9, 1)} psi` : `W = ${fmt(values.design_wheel_load || 10000, 0)} lb`;
  const diagramHeight = compact ? 360 : 380;
  const surfaceY = mode === "railroad" ? 116 : 108;
  const surfaceHeight = mode === "railroad" ? 16 : 24;
  const labelAllowance = compact ? 46 : 56;
  const coverIn = cover * 12;
  const verticalSpanIn = coverIn + (d + bd) / 2;
  const availableHeight = Math.max(120, diagramHeight - surfaceY - labelAllowance);
  const availableWidth = compact ? 188 : 224;
  const scale = Math.min(availableHeight / verticalSpanIn, availableWidth / bd);
  const pipeSize = Math.max(d * scale, 6);
  const boreSize = Math.max(bd * scale, pipeSize + 4);
  const scaledCoverHeight = coverIn * scale;
  const pipeTopY = surfaceY + scaledCoverHeight;
  const pipeCenterY = pipeTopY + pipeSize / 2;
  const boreTopY = pipeCenterY - boreSize / 2;
  const coverStartY = Math.min(surfaceY + surfaceHeight, Math.max(surfaceY, pipeTopY - 1));
  const coverLineHeight = Math.max(pipeTopY - coverStartY, 1);
  const pipeWallSize = Math.max(2, Math.min(8, tw * scale));
  const boreBorderSize = Math.max(2, Math.min(7, ((bd - d) / 2) * scale));
  const diagramStyle = {
    "--diagram-height": `${diagramHeight}px`,
    "--surface-y": `${surfaceY}px`,
    "--surface-height": `${surfaceHeight}px`,
    "--soil-y": `${surfaceY + surfaceHeight}px`,
    "--cover-start-y": `${coverStartY}px`,
    "--cover-height": `${coverLineHeight}px`,
    "--bore-top-y": `${boreTopY}px`,
    "--bore-size": `${boreSize}px`,
    "--pipe-size": `${pipeSize}px`,
    "--pipe-wall-size": `${pipeWallSize}px`,
    "--bore-border-size": `${boreBorderSize}px`
  } as React.CSSProperties;
  return (
      <div className={`diagram ${mode}${compact ? " compact" : ""}`} style={diagramStyle}>
        <div className="diagram-sky" />
        {mode === "railroad" ? (
          <>
            <div className="diagram-train" aria-hidden="true">
              <span className="train-engine" />
              <span className="train-car" />
              <span className="train-wheel a" />
              <span className="train-wheel b" />
              <span className="train-wheel c" />
              <span className="train-wheel d" />
            </div>
            <div className="diagram-track" aria-hidden="true">
              <span />
              <span />
              <i />
              <i />
              <i />
            </div>
          </>
        ) : (
          <>
            <div className="diagram-vehicle" aria-hidden="true">
              <span className="vehicle-cab" />
              <span className="vehicle-bed" />
              <span className="vehicle-wheel front" />
              <span className="vehicle-wheel rear" />
            </div>
            <div className="diagram-road-mark" aria-hidden="true" />
          </>
        )}
        <div className="diagram-load">{loadLabel}</div>
        <div className="diagram-surface">{mode === "railroad" ? "" : "Road surface"}</div>
        <div className="diagram-soil"><span>Soil / backfill</span></div>
        <div className="diagram-cover"><span>H = {fmt(cover, 1)} ft to top of pipe</span></div>
        <div className="diagram-bore">
          <div className="diagram-pipe"><span>D {fmt(d, 2)} in</span></div>
          <span className="diagram-bore-label">Bd {fmt(bd, 2)} in</span>
        </div>
      </div>
  );
}

function MiniResults({ result }: { result: Record<string, any> }) {
  return (
    <Panel>
      <SectionHeader title="Calculation Status" right={<ResultBadge value={result.overall_result || "Not Calculated"} />} />
      <div className="mini-result-list">
        {(result.checks || []).map((check: any) => (
          <div key={check.name}>
            <span>{check.name}</span>
            <strong>{(check.utilization * 100).toFixed(1)}%</strong>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ResultsPanel({ result, warnings }: { result: Record<string, any>; warnings: Array<Record<string, any>> }) {
  const checks = result.checks || [];
  const calculatedAt = formatDateTime(result.calculated_at);
  return (
    <Panel className="results-panel">
      <SectionHeader
        title="Results Summary"
        subtitle={`Pass/Fail evaluation per API RP 1102 - ${result.calculation_type || "Loading"}.`}
        right={
          <div className="result-head-actions">
            <span className="freshness-chip">{calculatedAt ? `Calculated ${calculatedAt}` : "Awaiting calculation"}</span>
            <span className="controlling-badge">Controlling: {result.controlling_check || "Not Calculated"}</span>
          </div>
        }
      />
      {warnings?.length ? (
        <div className="warning-callouts">
          {warnings.map((warning, index) => (
            <div className={`warning-callout ${warning.severity || "warning"}`} key={`${warning.code || "warning"}-${index}`}>
              <AlertTriangle size={16} />
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      ) : null}
      <table className="results-table">
        <thead><tr><th>Check</th><th>Calculated (psi)</th><th>Allowable (psi)</th><th>Utilization</th><th>Result</th></tr></thead>
        <tbody>
          {checks.map((check: any) => (
            <tr key={check.name}>
              <td>{check.name}</td>
              <td>{fmt(check.calculated_psi)}</td>
              <td>{fmt(check.allowable_psi)}</td>
              <td><UtilizationBar value={check.utilization} /> {(check.utilization * 100).toFixed(1)}%</td>
              <td><ResultBadge value={check.result} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function AdvancedPanel({ result, intermediate, warnings }: { result: Record<string, any>; intermediate: Record<string, any>; warnings: Array<Record<string, any>> }) {
  const values = firstIntermediate(intermediate);
  const isRail = result.calculation_type === "Railroad";
  const sections = [
    ["Internal Pressure", [["SHi Hoop (Barlow)", "SHi", "psi"], ["Allowable Hoop", "allowable_hoop", "psi"], ["SHi Pressurization", "SHi_internal", "psi"]]],
    ["Earth Load (Circumferential)", [["Khe Stiffness Factor", "Khe", ""], ["Be Burial Factor", "Be", ""], ["Ee Excavation Factor", "Ee", ""], ["SHe Stress from Earth Load", "SHe", "psi"]]],
    [`${isRail ? "Railroad" : "Highway"} Loading Factors`, [["Fi Impact Factor", "Fi", ""], ["KH Stiffness", values.KHh !== undefined ? "KHh" : "KHr", ""], ["GH Geometry", values.GHh !== undefined ? "GHh" : "GHr", ""], ["KL Stiffness", values.KLh !== undefined ? "KLh" : "KLr", ""]]],
    [`${isRail ? "Railroad" : "Highway"} Cyclic Stresses`, [["SH Cyclic Circumferential", "SH", "psi"], ["SL Cyclic Longitudinal", "SL", "psi"], ["Girth Weld Stress", "SFG", "psi"], ["Long. Weld Stress", "SFL", "psi"]]],
    ["Combined Stresses", [["S1 Max Circumferential", "S1", "psi"], ["S2 Max Longitudinal", "S2", "psi"], ["S3 Max Radial", "S3", "psi"], ["Seff Total Effective", "Seff", "psi"], ["Allowable Effective", "allowable_effective", "psi"]]],
    ["Fatigue / Welds", [["Allowable Girth Weld Stress", "allowable_girth", "psi"], ["Allowable Long. Weld Stress", "allowable_longitudinal", "psi"]]]
  ];

  return (
    <div className="screen-stack">
      <Panel>
        <SectionHeader
          title="Advanced Calculation View"
          subtitle="Intermediate variables, interpolated factors, and stresses. Click the info icon for the equation and reference."
          right={<span className="toggle-on">Show</span>}
        />
        <div className="advanced-grid">
          {sections.map(([title, rows]) => (
            <div className="advanced-card" key={String(title)}>
              <h3>{title}</h3>
              {(rows as string[][]).map(([label, key, unit]) => (
                <div className="advanced-row" key={label}>
                  <span>{label} <i title={advancedHelp[key] || label} aria-label={advancedHelp[key] || label}>i</i></span>
                  <strong>{fmt(values[key])} {unit}</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </Panel>
      {warnings?.length ? (
        <Panel>
          <SectionHeader title="Warnings" />
          {warnings.map((warning, index) => (
            <div className="warning-row" key={index}><AlertTriangle size={16} /> {warning.message}</div>
          ))}
        </Panel>
      ) : null}
    </div>
  );
}

function ExportHistory({ records, calc, scenario }: { records: ExportRecord[]; calc: Calculation; scenario: Scenario }) {
  return (
    <Panel>
      <SectionHeader
        title="Exports"
        subtitle="Recent calculation export records and scoped export actions."
        right={
          <div className="toolbar-actions">
            <Button href={`/api/exports/scenario/${scenario.id}.csv`} icon={<FileDown size={16} />}>Scenario CSV</Button>
            <Button href={`/api/exports/scenario/${scenario.id}.json`} icon={<FileDown size={16} />}>Scenario JSON</Button>
            <Button href={`/api/exports/calculation/${calc.id}.pdf`} variant="primary" icon={<FileDown size={16} />}>Calculation PDF</Button>
          </div>
        }
      />
      <div className="table-scroll">
        <table className="engineering-table export-records-table">
          <thead><tr><th>Type</th><th>File</th><th>Scenario</th><th>Exported</th></tr></thead>
          <tbody>
            {records.length ? records.map((record) => (
              <tr key={record.id}>
                <td>{record.export_type.toUpperCase()}</td>
                <td>{record.file_name}</td>
                <td>{record.scenario_id || "-"}</td>
                <td>{formatDate(record.exported_at)}</td>
              </tr>
            )) : (
              <tr><td colSpan={4}>No exports recorded yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function Standards() {
  const [data, setData] = useState<StandardsPayload | null>(null);
  useEffect(() => {
    api<StandardsPayload>("/standards/tables").then(setData).catch(console.error);
  }, []);
  const pavementFactors = data?.highway_loading_tables?.pavement_axle_factors || {};

  return (
    <div className="screen-stack">
      <PageTitle title="Standards & Lookup Tables" subtitle="Read-only engineering data used by the calculation engine." />
      <Panel className="tip-panel"><strong>Standards tables are read-only in the app.</strong> Updates require code changes, validation testing, and a version release.</Panel>
      <StandardsBlock icon={<Ruler size={18} />} title="Pipe Dimensions">
        <StandardsTable
          columns={["NPS", "D (in)", "tw Options (in)"]}
          rows={Object.entries(data?.pipe_dimensions || {}).map(([nps, pipe]: [string, any]) => [
            nps,
            fmt(pipe.outside_diameter, 3),
            (pipe.wall_thickness_options || []).map((item: number) => fmt(item, 3)).join(", ")
          ])}
        />
      </StandardsBlock>
      <StandardsBlock icon={<FileSpreadsheet size={18} />} title="Pipe Specifications, Grades & SMYS">
        <StandardsTable
          columns={["Specification", "Grade", "SMYS (psi)"]}
          rows={Object.entries(data?.pipe_grades || {}).flatMap(([specification, grades]: [string, any]) =>
            Object.entries(grades || {}).map(([grade, smys]) => [specification, grade, fmt(smys, 0)])
          )}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Layers size={18} />} title="Weld Seams & Joint Factor">
        <StandardsTable
          columns={["Weld Seam Type", "E"]}
          rows={Object.entries(data?.weld_seam_factors || {}).map(([name, factor]) => [name, fmt(factor, 3)])}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Database size={18} />} title="Soil Properties">
        <StandardsTable
          columns={["Soil Type", "E' (psi)", "Er (psi)"]}
          rows={Object.entries(data?.soil_properties || {}).map(([soil, values]: [string, any]) => [
            soil,
            fmt(values.e_prime, 0),
            fmt(values.er, 0)
          ])}
        />
      </StandardsBlock>
      <StandardsBlock icon={<ShieldCheck size={18} />} title="Design Factors">
        <StandardsTable
          columns={["Pipeline Location", "Class", "F"]}
          rows={Object.entries(data?.design_factors || {}).flatMap(([location, classes]: [string, any]) =>
            Object.entries(classes || {}).map(([classLocation, factor]) => [location, classLocation, fmt(factor, 3)])
          )}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Gauge size={18} />} title="Material Properties">
        <StandardsTable
          columns={["Material", "Es (psi)", "Poisson's Ratio", "Thermal Expansion"]}
          rows={Object.entries(data?.material_properties || {}).map(([material, values]: [string, any]) => [
            material,
            fmt(values.youngs_modulus, 0),
            fmt(values.poisson_ratio, 3),
            String(values.thermal_expansion)
          ])}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Table2 size={18} />} title="Highway Pavement & Axle Factors">
        <StandardsTable
          columns={["Case", "Pavement / Axle", "R", "L", "W (lb)"]}
          rows={Object.entries(pavementFactors).flatMap(([caseName, factors]: [string, any]) =>
            Object.entries(factors || {}).map(([label, values]: [string, any]) => [
              caseName === "shallow_small" ? "H < 4 ft and D <= 12 in" : "Standard",
              label,
              fmt(values.R, 3),
              fmt(values.L, 3),
              fmt(values.wheel_load, 0)
            ])
          )}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Calculator size={18} />} title="Fatigue Limit Examples">
        <StandardsTable
          columns={["Example", "Girth (psi)", "Longitudinal (psi)"]}
          rows={Object.entries(data?.fatigue_limit_examples || {}).map(([name, values]: [string, any]) => [
            name,
            fmt(values.girth, 0),
            fmt(values.longitudinal, 0)
          ])}
        />
      </StandardsBlock>
      <StandardsBlock icon={<Table2 size={18} />} title="Dropdown Options">
        <StandardsTable
          columns={["Control", "Available Values"]}
          rows={Object.entries(data?.dropdown_options || {})
            .filter(([name]) => !["calculation_statuses", "project_statuses"].includes(name))
            .map(([name, values]: [string, any]) => [
              labelize(name),
              Array.isArray(values) ? values.join(", ") : formatStandardValue(values)
            ])}
        />
      </StandardsBlock>
    </div>
  );
}

function StandardsBlock({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <Panel className="standard-section">
      <div className="standard-title">
        {icon}
        <h2>{title}</h2>
      </div>
      {children}
    </Panel>
  );
}

function StandardsTable({ columns, rows }: { columns: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="table-scroll">
      <table className="engineering-table standards-table">
        <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
        <tbody>
          {rows.length ? rows.map((row, index) => (
            <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>
          )) : (
            <tr><td colSpan={columns.length}>Loading standards data...</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function References() {
  const refs = [
    ["API Recommended Practice 1102, 7th Edition, December 2007 (Reaffirmed 2024)", "Steel Pipelines Crossing Railroads and Highways. Primary technical basis for loading, stiffness, burial, excavation geometry, impact, and fatigue calculations."],
    ["49 CFR Part 192 Subpart C - Pipe Design", "U.S. federal pipeline safety regulations governing design factor F and longitudinal joint factor E."],
    ["ASME B31.8 - Gas Transmission and Distribution Piping Systems", "Industry consensus standard. Chapter 4 defines design factor F by location and class."],
    ["Copy of API 1102 Highway.xlsx", "Source workbook used to port highway formulas, tables, defaults, and validation cases."],
    ["Copy of API 1102 Railroad.xlsx", "Source workbook used to port railroad formulas, tables, defaults, and validation cases."]
  ];
  return (
    <div className="screen-stack">
      <PageTitle title="References" subtitle="Source standards and references used by this tool." />
      <Panel>
        <SectionHeader title="Source Standards" />
        <div className="reference-list">
          {refs.map(([title, text]) => (
            <div className="reference-row" key={title}>
              <div><strong>{title}</strong><p>{text}</p></div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function About() {
  return (
    <div className="screen-stack">
      <Panel className="about-panel">
        <img src={hdrLogo} alt="HDR" />
        <div>
          <h1>API RP 1102 Loading Calculator</h1>
          <p>HDR internal engineering calculation tool for gas pipeline highway and railroad crossing checks.</p>
          <div className="about-meta">
            <span>App version: v0.1.0</span>
            <span>Calculation engine: v0.1.0</span>
            <span>Source workbooks: Copy of API 1102 Highway / Railroad</span>
          </div>
        </div>
      </Panel>
      <Panel>
        <SectionHeader title="Engineering Disclaimer" />
        <p className="disclaimer">This tool is intended to support engineering calculations and documentation. It does not replace engineering judgment, applicable codes, standards, client requirements, or independent checking.</p>
      </Panel>
    </div>
  );
}

function ReportPreview({ calc, project, scenario, onBack }: { calc: Calculation; project: Project | null; scenario: Scenario; onBack: () => void }) {
  const values = firstIntermediate(scenario.intermediate_values);
  const checks = scenario.results?.checks || [];
  const loadingType = `${calc.calculation_type} Loading`;
  return (
    <div className="report-screen">
      <div className="report-toolbar">
        <Button icon={<ArrowLeft size={16} />} onClick={onBack}>Back to Calculation</Button>
        <div className="report-toolbar-center">
          <span className="report-type-chip">{loadingType}</span>
        </div>
        <div className="toolbar-actions">
          <Button href={`/api/exports/calculation/${calc.id}.csv`} icon={<FileDown size={16} />}>Export CSV</Button>
          <Button href={`/api/exports/calculation/${calc.id}.json`} icon={<FileDown size={16} />}>Export JSON</Button>
          <Button variant="primary" icon={<Printer size={16} />} onClick={() => window.print()}>Print / PDF</Button>
        </div>
      </div>
      <article className="report-page">
        <header className="report-header">
          <div className="report-logo-block">
            <img src={hdrLogo} alt="HDR" />
            <span>API RP 1102 {calc.calculation_type} Loading Calculator</span>
            <small>Gas Pipeline - Technical Tool</small>
          </div>
          <div>
            <small>Engineering Calculation Package</small>
            <h1>API RP 1102 {calc.calculation_type} Loading Analysis</h1>
            <p>Calc {calc.calc_number} - Rev {calc.revision || "0"} - {calc.date || "2026-05-24"} - {calc.status}</p>
          </div>
        </header>
        <div className="report-grid">
          <ReportBox title="Project & Calculation" rows={[
            ["Project", project?.project_name || `Project ${calc.project_id}`],
            ["Project No.", project?.project_number || "-"],
            ["Client", project?.client || "-"],
            ["Location", project?.location || "-"],
            ["Crossing", calc.crossing_name],
            ["Calc No.", calc.calc_number],
            ["Date", calc.date || "-"],
            ["Crossing Type", calc.calculation_type],
            ["Scenario", scenario.scenario_name || "Base Case"],
            ["Prepared By", calc.prepared_by || "-"],
            ["Checked By", calc.checked_by || "-"],
            ["Status", calc.status]
          ]} />
          <ReportBox title="Purpose & References" rows={[
            ["Basis", "API RP 1102, 7th Ed. (2007, R2024)"],
            ["Purpose", `Check combined stress of buried gas pipeline crossing under internal pressure and external ${calc.calculation_type.toLowerCase()} loading.`],
            ["References", "49 CFR Part 192, ASME B31.8, source workbooks"],
            ["Notes", calc.notes || "Allowables per API RP 1102 tables and ASME B31.8 design factor."]
          ]} />
          <ReportBox title="Inputs & Assumptions" rows={[
            ["NPS", values.nps || "12"],
            ["O.D. D (in)", fmt(values.outside_diameter || 12.75, 2)],
            ["Wall tw (in)", fmt(values.wall_thickness || 0.25, 3)],
            ["Cover H (ft)", fmt(values.cover_depth || 6, 2)],
            ["Bd/D", fmt(values.bd_d || 1.157, 3)],
            ["H/Bd", fmt(values.h_bd || 4.881, 3)],
            ["Spec / Grade", `${values.pipe_specification || "API 5L"} / ${values.pipe_grade || "X65"}`],
            ["SMYS (psi)", fmt(values.smys || 65000)],
            ["Joint Factor E", fmt(values.joint_factor || 1, 3)],
            ["Pressure P (psi)", fmt(values.operating_pressure || 1000)],
            ["Soil Type", values.soil_type || "Loose sands and gravels"],
            [calc.calculation_type === "Railroad" ? "Surface Pressure w (psi)" : "Design Wheel Load W (lb)", fmt(calc.calculation_type === "Railroad" ? values.surface_pressure || 13.9 : values.design_wheel_load || 10000, calc.calculation_type === "Railroad" ? 1 : 0)]
          ]} />
          <ReportBox title="Intermediate Calculations" rows={[
            ["Sh Hoop (Barlow)", `${fmt(values.SHi)} psi`],
            ["Allowable Hoop", `${fmt(values.allowable_hoop)} psi`],
            ["Khe", fmt(values.Khe, 3)],
            ["Be", fmt(values.Be, 3)],
            ["Ee", fmt(values.Ee, 3)],
            ["SHe", `${fmt(values.SHe)} psi`],
            ["Fi", fmt(values.Fi, 3)],
            ["S1 / S2 / S3", `${fmt(values.S1)} / ${fmt(values.S2)} / ${fmt(values.S3)}`],
            ["Seff", `${fmt(values.Seff)} psi`],
            ["Allowable Effective", `${fmt(values.allowable_effective)} psi`],
            ["Allow. Girth / Long.", `${fmt(values.allowable_girth)} / ${fmt(values.allowable_longitudinal)} psi`]
          ]} />
        </div>
        <div className="report-lower-grid">
          <section className="report-schematic">
            <h2>Pipeline Cross-Section Schematic</h2>
            <div className="report-diagram-frame">
              <CrossSectionDiagram mode={calc.calculation_type === "Railroad" ? "railroad" : "highway"} values={values} compact />
            </div>
          </section>
          <section className="report-results-section">
            <h2 className="report-section-title">Results Summary</h2>
            <table className="report-results">
              <thead><tr><th>Check</th><th>Calculated</th><th>Allowable</th><th>Utilization</th><th>Result</th></tr></thead>
              <tbody>{checks.map((check: any) => <tr key={check.name}><td>{check.name}</td><td>{fmt(check.calculated_psi)}</td><td>{fmt(check.allowable_psi)}</td><td>{(check.utilization * 100).toFixed(1)}%</td><td>{check.result}</td></tr>)}</tbody>
            </table>
          </section>
        </div>
        <p className="report-disclaimer">Engineering Disclaimer: This tool supports engineering calculations and documentation. It does not replace engineering judgment, applicable codes, standards, client requirements, or independent checking.</p>
      </article>
    </div>
  );
}

function ReportBox({ title, rows }: { title: string; rows: string[][] }) {
  return (
    <section className="report-box">
      <h2>{title}</h2>
      <table>
        <tbody>{rows.map(([label, value]) => <tr key={label}><th>{label}</th><td>{value}</td></tr>)}</tbody>
      </table>
    </section>
  );
}

function ImportProjectButton({ onImport, compact = false }: { onImport: (file: File) => void; compact?: boolean }) {
  return (
    <label className="ui-button secondary">
      <Upload size={compact ? 16 : 17} />
      Import Project
      <input
        className="hidden-file-input"
        type="file"
        accept=".json,.hdr1102.json,application/json"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onImport(file);
          event.currentTarget.value = "";
        }}
      />
    </label>
  );
}

function keys(source: Record<string, any> | undefined, fallback: Array<string | number>) {
  const values = Object.keys(source || {});
  return values.length ? values : fallback;
}

function nextPipeSelection(nps: string, currentWallThickness: any, currentBoredDiameter: any, pipeDimensions: Record<string, any>) {
  const pipeInfo = pipeDimensions?.[nps] || {};
  const wallOptions = pipeInfo.wall_thickness_options || [];
  const current = Number(currentWallThickness);
  const outsideDiameter = Number(pipeInfo.outside_diameter);
  const boredDiameter = Number(currentBoredDiameter);
  const next: Record<string, any> = {
    nps,
    outside_diameter: Number.isFinite(outsideDiameter) ? outsideDiameter : undefined,
    wall_thickness: Number.isFinite(current) && current > 0 ? current : wallOptions[0] || 0.25
  };
  if (Number.isFinite(outsideDiameter) && (!Number.isFinite(boredDiameter) || boredDiameter <= outsideDiameter)) {
    next.bored_diameter = Number((outsideDiameter + 2).toFixed(3));
  }
  return next;
}

function nextSpecificationSelection(specification: string, currentGrade: any, pipeGrades: Record<string, any>) {
  const gradeOptions = Object.keys(pipeGrades?.[specification] || {});
  const grade = gradeOptions.includes(String(currentGrade)) ? String(currentGrade) : gradeOptions[0] || "X65";
  return { pipe_specification: specification, pipe_grade: grade };
}

function firstIntermediate(intermediate: Record<string, any> = {}) {
  return intermediate.highway || intermediate.railroad || intermediate || {};
}

function recentProjects(projects: Project[], calculations: Calculation[]) {
  return [...projects]
    .sort((a, b) => (new Date(b.updated_at || b.created_at || 0).getTime() || 0) - (new Date(a.updated_at || a.created_at || 0).getTime() || 0))
    .slice(0, 3)
    .filter((project) => projectCalcCount(project.id, calculations) >= 0);
}

function projectCalcCount(projectId: number, calculations: Calculation[]) {
  return calculations.filter((calc) => calc.project_id === projectId).length;
}

function formatDate(value: string) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function formatDateTime(value: string) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
}

function fmt(value: any, digits = 1) {
  const number = Number(value || 0);
  return number.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits > 1 ? Math.min(digits, 3) : 0 });
}

function numeric(value: any) {
  const number = Number(value);
  return Number.isNaN(number) ? value : number;
}

function labelize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatStandardValue(value: any) {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") {
    if ("outside_diameter" in value) return `OD ${value.outside_diameter}`;
    if ("girth" in value) return `Girth ${value.girth}, Long. ${value.longitudinal}`;
    return JSON.stringify(value);
  }
  return String(value);
}

createRoot(document.getElementById("root")!).render(<App />);
