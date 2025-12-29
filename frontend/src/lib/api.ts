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
};

const DEFAULT_BACKEND_BASE = 'http://127.0.0.1:8001';

function backendBaseUrl(): string {
  // Keep this file Jest-safe: do not reference `import.meta` (Jest runs in CJS).
  // In Vite you can keep the default, or inject a runtime override on window.
  const windowOverride =
    typeof window !== 'undefined'
      ? (window as unknown as { __BACKEND_BASE_URL__?: string }).__BACKEND_BASE_URL__
      : undefined;

  return windowOverride || (typeof process !== 'undefined' ? (process.env.VITE_BACKEND_URL as string | undefined) : undefined) || DEFAULT_BACKEND_BASE;
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
    const text = await resp.text().catch(() => '');
    throw new Error(text || `Request failed (${resp.status})`);
  }

  return (await resp.json()) as HomeworkHelpJsonRes;
}
