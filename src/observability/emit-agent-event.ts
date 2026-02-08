import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { randomUUID } from 'node:crypto';
import { execSync } from 'node:child_process';
import { validateAgentEvent } from './agent-event.schema.ts';
import type { AgentEvent, AgentEventType, AgentEventStatus, AgentEventPayload } from './agent-event.schema.ts';

type EmitOptions = {
  filePath?: string;
  strict?: boolean;
};

type CreateEventInput = {
  event_type: AgentEventType;
  status: AgentEventStatus;
  duration_ms: number;
  payload: AgentEventPayload;
  correlation_id?: string;
};

function readGitSha(): string {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch (_error) {
    return 'unknown';
  }
}

function readBranch(): string {
  if (process.env.GITHUB_REF_NAME) return process.env.GITHUB_REF_NAME;
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
  } catch (_error) {
    return 'unknown';
  }
}

function resolveCorrelationId(input?: string): string {
  return (
    input ||
    process.env.CORRELATION_ID ||
    process.env.GITHUB_RUN_ID ||
    randomUUID()
  );
}

function defaultEventPath(): string {
  const date = new Date().toISOString().slice(0, 10);
  return path.join('artifacts', 'events', `durability-${date}.ndjson`);
}

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export function createAgentEvent(input: CreateEventInput): AgentEvent {
  return {
    event_version: 'v1',
    event_type: input.event_type,
    timestamp: new Date().toISOString(),
    commit_sha: readGitSha(),
    branch: readBranch(),
    status: input.status,
    duration_ms: input.duration_ms,
    correlation_id: resolveCorrelationId(input.correlation_id),
    payload: input.payload
  };
}

export function emitAgentEvent(event: AgentEvent, options: EmitOptions = {}): void {
  const { valid, errors } = validateAgentEvent(event);
  if (!valid) {
    const message = `Event schema validation failed: ${errors.join('; ')}`;
    if (options.strict) {
      throw new Error(message);
    }
    console.warn(message);
  }

  const filePath = options.filePath ?? defaultEventPath();
  ensureDir(filePath);
  fs.appendFileSync(filePath, `${JSON.stringify(event)}${os.EOL}`);
}
