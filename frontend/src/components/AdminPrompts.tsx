import { useState, useEffect, useCallback } from 'react';
import {
  adminListPrompts, adminListVersions, adminGetVersion, adminSavePrompt, adminTryPrompt,
  type PromptSummary, type PromptVersion,
} from '../lib/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const PROMPT_LABELS: Record<string, string> = {
  ingestion: 'Problem ingestion',
  similar: 'Similar-problem generation',
  score: 'Explanation scoring',
  classify: 'Wrong-answer classification',
};

export function AdminPrompts() {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem('adminKey') ?? '');
  const [keyInput, setKeyInput] = useState('');
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [promptContent, setPromptContent] = useState<Record<string, PromptVersion>>({});
  const [loadError, setLoadError] = useState('');

  // Editor state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [systemText, setSystemText] = useState('');
  const [userText, setUserText] = useState('');
  const [notes, setNotes] = useState('');
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  // Test panel state
  const [testInput, setTestInput] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ json: string; durationMs: number } | null>(null);
  const [testError, setTestError] = useState('');

  const loadPrompts = useCallback(async (key: string) => {
    setLoadError('');
    try {
      const list = await adminListPrompts(key);
      setPrompts(list);
      // Fetch active content for each seeded prompt
      const content: Record<string, PromptVersion> = {};
      await Promise.all(
        list
          .filter(p => p.activeVersion != null)
          .map(async p => {
            try {
              content[p.promptId] = await adminGetVersion(key, p.promptId, p.activeVersion!);
            } catch { /* ignore individual failures */ }
          })
      );
      setPromptContent(content);
    } catch (e: any) {
      setLoadError(e.message ?? 'Failed to load');
    }
  }, []);

  const handleKeySubmit = () => {
    sessionStorage.setItem('adminKey', keyInput);
    setAdminKey(keyInput);
    loadPrompts(keyInput);
  };

  useEffect(() => {
    if (adminKey) loadPrompts(adminKey);
  }, [adminKey, loadPrompts]);

  const openEditor = async (promptId: string) => {
    setEditingId(promptId);
    setSaveMsg('');
    setTestResult(null);
    setTestError('');
    const vlist = await adminListVersions(adminKey, promptId);
    setVersions(vlist);
    if (vlist.length > 0) {
      const latest = vlist[vlist.length - 1];
      setSystemText(latest.systemPrompt);
      setUserText(latest.userPromptTemplate);
    } else {
      setSystemText('');
      setUserText('');
    }
    setNotes('');
  };

  const loadVersion = (v: PromptVersion) => {
    setSystemText(v.systemPrompt);
    setUserText(v.userPromptTemplate);
    setSaveMsg('');
  };

  const handleSave = async () => {
    if (!editingId) return;
    setSaving(true);
    setSaveMsg('');
    try {
      const res = await adminSavePrompt(adminKey, editingId, {
        systemPrompt: systemText,
        userPromptTemplate: userText,
        notes,
      });
      setSaveMsg(`Saved as version ${res.version}`);
      setNotes('');
      const vlist = await adminListVersions(adminKey, editingId);
      setVersions(vlist);
      loadPrompts(adminKey);
    } catch (e: any) {
      setSaveMsg(`Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTry = async () => {
    if (!editingId || !testInput.trim()) return;
    setTesting(true);
    setTestResult(null);
    setTestError('');
    try {
      const res = await adminTryPrompt(adminKey, editingId, {
        systemPrompt: systemText,
        userPromptTemplate: userText,
        testInput,
      });
      setTestResult({ json: JSON.stringify(res.result, null, 2), durationMs: res.durationMs });
    } catch (e: any) {
      setTestError(e.message ?? 'Failed');
    } finally {
      setTesting(false);
    }
  };

  // Key entry screen
  if (!adminKey) {
    return (
      <div className="max-w-sm mx-auto mt-24 space-y-3">
        <h1 className="text-xl font-semibold">Admin</h1>
        <Input
          type="password"
          placeholder="Admin key"
          value={keyInput}
          onChange={e => setKeyInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleKeySubmit()}
        />
        <Button onClick={handleKeySubmit} disabled={!keyInput}>Enter</Button>
      </div>
    );
  }

  // Editor screen
  if (editingId) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-6 space-y-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}>← Back</Button>
          <h1 className="text-xl font-semibold">{PROMPT_LABELS[editingId] ?? editingId}</h1>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Editor — takes 2/3 width */}
          <div className="col-span-2 space-y-3">
            <div className="space-y-1">
              <label className="text-sm font-medium">System prompt</label>
              <Textarea
                value={systemText}
                onChange={e => setSystemText(e.target.value)}
                className="font-mono text-sm min-h-32 resize-y"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">
                User prompt template{' '}
                <span className="text-gray-400 font-normal">({'{{BASE_STRUCTURE}}'} is replaced at runtime)</span>
              </label>
              <Textarea
                value={userText}
                onChange={e => setUserText(e.target.value)}
                className="font-mono text-sm min-h-48 resize-y"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Notes (optional)</label>
              <Input
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="What changed in this version?"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save as new version'}
              </Button>
              {saveMsg && (
                <span className={`text-sm ${saveMsg.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>
                  {saveMsg}
                </span>
              )}
            </div>
          </div>

          {/* Version history — 1/3 width */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Version history</p>
            {versions.length === 0 && <p className="text-sm text-gray-400">No versions yet</p>}
            {[...versions].reverse().map(v => (
              <Card
                key={v.version}
                className="cursor-pointer hover:border-blue-400 transition-colors"
                onClick={() => loadVersion(v)}
              >
                <CardContent className="p-3 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">v{v.version}</span>
                    <Badge variant="outline" className="text-xs">{v.createdBy}</Badge>
                  </div>
                  <p className="text-xs text-gray-500">{new Date(v.createdAt).toLocaleString()}</p>
                  {v.notes && <p className="text-xs text-gray-600 truncate">{v.notes}</p>}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Test panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Test panel</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="Enter a problem, e.g. 2x + 5 = 17"
                value={testInput}
                onChange={e => setTestInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !testing && handleTry()}
                className="flex-1"
              />
              <Button onClick={handleTry} disabled={testing || !testInput.trim()}>
                {testing ? 'Running…' : 'Run'}
              </Button>
            </div>
            <p className="text-xs text-gray-400">
              Runs the <em>current editor content</em> (unsaved changes included). Uses the live OpenAI API — each run costs tokens.
            </p>
            {testError && <p className="text-sm text-red-600">{testError}</p>}
            {testResult && (
              <div className="space-y-1">
                <p className="text-xs text-gray-500">{testResult.durationMs}ms</p>
                <pre className="text-xs bg-gray-50 border rounded p-3 overflow-auto max-h-96 whitespace-pre-wrap">
                  {testResult.json}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // List screen
  return (
    <div className="max-w-2xl mx-auto px-6 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Prompts</h1>
        <Button variant="ghost" size="sm" onClick={() => { sessionStorage.removeItem('adminKey'); setAdminKey(''); }}>
          Sign out
        </Button>
      </div>
      {loadError && <p className="text-sm text-red-600">{loadError}</p>}
      <div className="space-y-4">
        {prompts.map(p => {
          const content = promptContent[p.promptId];
          return (
            <Card key={p.promptId}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{PROMPT_LABELS[p.promptId] ?? p.promptId}</CardTitle>
                  <div className="flex items-center gap-2">
                    {p.activeVersion != null
                      ? <Badge>v{p.activeVersion}</Badge>
                      : <Badge variant="secondary">Not seeded</Badge>
                    }
                    <Button size="sm" variant="outline" onClick={() => openEditor(p.promptId)}>
                      Edit
                    </Button>
                  </div>
                </div>
                {p.updatedAt && (
                  <p className="text-xs text-gray-400">Last updated {new Date(p.updatedAt).toLocaleString()}</p>
                )}
              </CardHeader>
              {content ? (
                <CardContent className="space-y-3 pt-0">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">System prompt</p>
                    <pre className="text-xs bg-gray-50 border rounded p-3 whitespace-pre-wrap font-mono leading-relaxed">
                      {content.systemPrompt}
                    </pre>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">User prompt template</p>
                    <pre className="text-xs bg-gray-50 border rounded p-3 whitespace-pre-wrap font-mono leading-relaxed">
                      {content.userPromptTemplate}
                    </pre>
                  </div>
                </CardContent>
              ) : p.activeVersion == null ? (
                <CardContent className="pt-0">
                  <p className="text-sm text-gray-400">Not yet seeded — restart the backend to seed this prompt.</p>
                </CardContent>
              ) : null}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
