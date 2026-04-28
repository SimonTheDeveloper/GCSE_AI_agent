export type HomeworkHelpJsonReq = {
  uid: string;
  text: string;
  yearGroup?: number | null;
  tier?: string;
  desiredHelpLevel?: string;
  useCache?: boolean;
};

export type HomeworkHelpJsonRes = {
  result: any;
  problem_id?: string | null;
  attempt_id?: string | null;
};

export type CommonErrorIn = {
  category: string;
  pattern: string;
  wrong_answer_example: string;
  redirect_question: string;
};

export type ClassifyAnswerReq = {
  attempt_id: string;
  step_number: number;
  raw_input: string;
  expected_answer: string;
  common_errors: CommonErrorIn[];
};

export type ClassifyAnswerRes = {
  is_correct: boolean;
  error_category?: string | null;
  redirect_question?: string | null;
  matched_pattern?: string | null;
};

export type LogEventReq = {
  attempt_id: string;
  event_type: string;
  step_number: number;
  payload?: Record<string, unknown>;
};

const DEFAULT_BACKEND_BASE = 'http://127.0.0.1:8001';

function backendBaseUrl(): string {
  // Keep this file Jest-safe: do not reference `import.meta` (Jest runs in CJS).
  // In production, config.js (deployed by CDK) sets window.__BACKEND_BASE_URL__ = ''
  // so that API calls use a relative path routed through CloudFront to the ALB.
  if (typeof window !== 'undefined' && '__BACKEND_BASE_URL__' in (window as unknown as object)) {
    return (window as unknown as { __BACKEND_BASE_URL__: string }).__BACKEND_BASE_URL__;
  }
  return (typeof process !== 'undefined' ? (process.env.VITE_BACKEND_URL as string | undefined) : undefined) || DEFAULT_BACKEND_BASE;
}

// Admin prompt management

export type PromptSummary = {
  promptId: string;
  activeVersion: number | null;
  updatedAt: string | null;
};

export type PromptVersion = {
  promptId: string;
  version: number;
  systemPrompt: string;
  userPromptTemplate: string;
  createdAt: string;
  createdBy: string;
  notes: string;
};

export type PromptSaveReq = {
  systemPrompt: string;
  userPromptTemplate: string;
  notes?: string;
};

export type PromptTryReq = {
  systemPrompt: string;
  userPromptTemplate: string;
  testInput: string;
};

export type PromptTryRes = {
  result: any;
  promptVersion: number;
  durationMs: number;
};

async function adminFetch(path: string, adminKey: string, init?: RequestInit): Promise<Response> {
  const resp = await fetch(`${backendBaseUrl()}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Key': adminKey,
      ...(init?.headers ?? {}),
    },
  });
  if (!resp.ok) {
    let message = '';
    try {
      const data = await resp.json();
      if (data?.detail) message = String(data.detail);
    } catch { message = await resp.text().catch(() => ''); }
    throw new Error(message || `Request failed (${resp.status})`);
  }
  return resp;
}

export async function adminListPrompts(adminKey: string): Promise<PromptSummary[]> {
  const resp = await adminFetch('/api/v1/admin/prompts', adminKey);
  return resp.json();
}

export async function adminListVersions(adminKey: string, promptId: string): Promise<PromptVersion[]> {
  const resp = await adminFetch(`/api/v1/admin/prompts/${promptId}/versions`, adminKey);
  return resp.json();
}

export async function adminGetVersion(adminKey: string, promptId: string, version: number): Promise<PromptVersion> {
  const resp = await adminFetch(`/api/v1/admin/prompts/${promptId}/versions/${version}`, adminKey);
  return resp.json();
}

export async function adminSavePrompt(adminKey: string, promptId: string, req: PromptSaveReq): Promise<{ promptId: string; version: number }> {
  const resp = await adminFetch(`/api/v1/admin/prompts/${promptId}`, adminKey, {
    method: 'PUT',
    body: JSON.stringify(req),
  });
  return resp.json();
}

export async function adminTryPrompt(adminKey: string, promptId: string, req: PromptTryReq): Promise<PromptTryRes> {
  const resp = await adminFetch(`/api/v1/admin/prompts/${promptId}/try`, adminKey, {
    method: 'POST',
    body: JSON.stringify(req),
  });
  return resp.json();
}

export async function classifyAnswer(req: ClassifyAnswerReq): Promise<ClassifyAnswerRes> {
  const resp = await fetch(`${backendBaseUrl()}/api/v1/homework/classify-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!resp.ok) throw new Error(`classify-answer failed (${resp.status})`);
  return resp.json();
}

export async function logEvent(req: LogEventReq): Promise<void> {
  await fetch(`${backendBaseUrl()}/api/v1/homework/log-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function postHomeworkHelpJson(req: HomeworkHelpJsonReq): Promise<HomeworkHelpJsonRes> {
  const resp = await fetch(`${backendBaseUrl()}/api/v1/homework/help-json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req),
  });

  if (!resp.ok) {
    // FastAPI typically returns {"detail": "..."} on errors.
    let message = '';
    try {
      const data = (await resp.json()) as any;
      if (data && typeof data.detail === 'string') message = data.detail;
    } catch {
      // fall back to text
      message = await resp.text().catch(() => '');
    }
    throw new Error(message || `Request failed (${resp.status})`);
  }

  return (await resp.json()) as HomeworkHelpJsonRes;
}
