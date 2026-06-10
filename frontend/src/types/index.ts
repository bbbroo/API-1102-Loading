export type DashboardRow = {
  id: number;
  calc_number: string;
  project: string;
  crossing_name: string;
  calculation_type: string;
  status: string;
  result: string;
  modified_date: string;
  prepared_by: string;
  checked_by: string;
  reviewer: string;
  pipe_size: string;
};

export type DashboardSummary = {
  total_projects: number;
  total_calculations: number;
  recent_activity: number;
  recent: DashboardRow[];
};

export type Project = {
  id: number;
  project_name: string;
  project_number: string;
  client: string;
  location: string;
  description: string;
  status: string;
  created_at?: string;
  updated_at?: string;
};

export type Calculation = {
  id: number;
  project_id: number;
  calc_number: string;
  crossing_name: string;
  calculation_type: string;
  road_highway: string;
  railroad_route: string;
  prepared_by: string;
  checked_by: string;
  reviewer: string;
  date?: string | null;
  revision: string;
  status: string;
  review_comments: string;
  notes: string;
  overall_result: string;
  controlling_check: string;
};

export type Scenario = {
  id: number;
  calculation_id: number;
  scenario_name: string;
  description: string;
  shared_inputs: Record<string, any>;
  highway_inputs: Record<string, any>;
  railroad_inputs: Record<string, any>;
  results: Record<string, any>;
  intermediate_values: Record<string, any>;
  warnings: Array<Record<string, any>>;
};

export type ExportRecord = {
  id: number;
  calculation_id: number;
  scenario_id: number | null;
  export_type: string;
  file_name: string;
  exported_at: string;
};
