export type AgentEventType =
  | 'tool_parity_check'
  | 'schema_contract_check'
  | 'benchmark_run'
  | 'budget_gate';

export type AgentEventStatus = 'pass' | 'fail';

export type ToolParityPayload = {
  tools_manifest: number;
  tools_runtime: number;
  mismatch_count: number;
  mismatches?: string[];
  failure_reason?: string;
};

export type SchemaContractPayload = {
  tools_checked: number;
  matching: number;
  drifted: number;
  missing: number;
  orphaned: number;
  breaking_changes: number;
  non_breaking_changes: number;
  drifted_tools?: string[];
  missing_tools?: string[];
  orphaned_tools?: string[];
  failure_reason?: string;
};

export type BenchmarkRunPayload = {
  mode: 'deterministic' | 'real';
  p50_ms: number;
  p95_ms: number;
  error_rate: number;
  seed: string;
  node_version: string;
  runner_os: string;
};

export type BudgetGatePayload = {
  mode: 'deterministic' | 'real';
  p50_ms: number;
  p95_ms: number;
  error_rate: number;
  baseline_p95_ms: number;
  threshold_p95_ms: number;
  regression_pct: number;
  seed: string;
  node_version: string;
  runner_os: string;
  failure_reason?: string;
  skipped?: boolean;
};

export type AgentEventPayload =
  | ToolParityPayload
  | SchemaContractPayload
  | BenchmarkRunPayload
  | BudgetGatePayload;

export type AgentEvent = {
  event_version: 'v1';
  event_type: AgentEventType;
  timestamp: string;
  commit_sha: string;
  branch: string;
  status: AgentEventStatus;
  duration_ms: number;
  correlation_id: string;
  payload: AgentEventPayload;
};

type ValidationResult = {
  valid: boolean;
  errors: string[];
};

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function validateToolParityPayload(payload: Record<string, unknown>, errors: string[]): void {
  if (!isNumber(payload.tools_manifest)) errors.push('payload.tools_manifest must be a number');
  if (!isNumber(payload.tools_runtime)) errors.push('payload.tools_runtime must be a number');
  if (!isNumber(payload.mismatch_count)) errors.push('payload.mismatch_count must be a number');
  if (payload.mismatches != null && !Array.isArray(payload.mismatches)) {
    errors.push('payload.mismatches must be an array when provided');
  }
}

function validateSchemaContractPayload(payload: Record<string, unknown>, errors: string[]): void {
  if (!isNumber(payload.tools_checked)) errors.push('payload.tools_checked must be a number');
  if (!isNumber(payload.matching)) errors.push('payload.matching must be a number');
  if (!isNumber(payload.drifted)) errors.push('payload.drifted must be a number');
  if (!isNumber(payload.missing)) errors.push('payload.missing must be a number');
  if (!isNumber(payload.orphaned)) errors.push('payload.orphaned must be a number');
  if (!isNumber(payload.breaking_changes)) errors.push('payload.breaking_changes must be a number');
  if (!isNumber(payload.non_breaking_changes)) errors.push('payload.non_breaking_changes must be a number');
}

function validateBenchmarkRunPayload(payload: Record<string, unknown>, errors: string[]): void {
  if (payload.mode !== 'deterministic' && payload.mode !== 'real') {
    errors.push("payload.mode must be 'deterministic' or 'real'");
  }
  if (!isNumber(payload.p50_ms)) errors.push('payload.p50_ms must be a number');
  if (!isNumber(payload.p95_ms)) errors.push('payload.p95_ms must be a number');
  if (!isNumber(payload.error_rate)) errors.push('payload.error_rate must be a number');
  if (!isString(payload.seed)) errors.push('payload.seed must be a non-empty string');
  if (!isString(payload.node_version)) errors.push('payload.node_version must be a non-empty string');
  if (!isString(payload.runner_os)) errors.push('payload.runner_os must be a non-empty string');
}

function validateBudgetGatePayload(payload: Record<string, unknown>, errors: string[]): void {
  validateBenchmarkRunPayload(payload, errors);
  if (!isNumber(payload.baseline_p95_ms)) errors.push('payload.baseline_p95_ms must be a number');
  if (!isNumber(payload.threshold_p95_ms)) errors.push('payload.threshold_p95_ms must be a number');
  if (!isNumber(payload.regression_pct)) errors.push('payload.regression_pct must be a number');
  if (payload.skipped != null && typeof payload.skipped !== 'boolean') {
    errors.push('payload.skipped must be a boolean when provided');
  }
}

export function validateAgentEvent(event: unknown): ValidationResult {
  const errors: string[] = [];

  if (!isObject(event)) {
    return { valid: false, errors: ['event must be an object'] };
  }

  if (event.event_version !== 'v1') errors.push("event_version must be 'v1'");
  if (!isString(event.timestamp)) errors.push('timestamp must be a non-empty string');
  if (!isString(event.commit_sha)) errors.push('commit_sha must be a non-empty string');
  if (!isString(event.branch)) errors.push('branch must be a non-empty string');
  if (event.status !== 'pass' && event.status !== 'fail') errors.push("status must be 'pass' or 'fail'");
  if (!isNumber(event.duration_ms)) errors.push('duration_ms must be a number');
  if (!isString(event.correlation_id)) errors.push('correlation_id must be a non-empty string');

  const eventType = event.event_type as AgentEventType | undefined;
  if (!eventType || !['tool_parity_check', 'schema_contract_check', 'benchmark_run', 'budget_gate'].includes(eventType)) {
    errors.push('event_type must be a valid durability event type');
  }

  if (!isObject(event.payload)) {
    errors.push('payload must be an object');
  } else if (eventType) {
    switch (eventType) {
      case 'tool_parity_check':
        validateToolParityPayload(event.payload, errors);
        break;
      case 'schema_contract_check':
        validateSchemaContractPayload(event.payload, errors);
        break;
      case 'benchmark_run':
        validateBenchmarkRunPayload(event.payload, errors);
        break;
      case 'budget_gate':
        validateBudgetGatePayload(event.payload, errors);
        break;
    }
  }

  return { valid: errors.length === 0, errors };
}
