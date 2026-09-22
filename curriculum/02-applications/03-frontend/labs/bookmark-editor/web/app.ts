type Bookmark = {id: string; title: string; url: string; created_at: number; version: number};
export {}; // This file is loaded as an ES module in index.html.
type Page = {items: Bookmark[]; nextCursor: string | null};
type Pending = {key: string; title: string; revision: number; expectedVersion: number; generation: number};
const get = <T extends HTMLElement>(id: string): T => document.getElementById(id) as T;
const title = get<HTMLInputElement>('title');
const save = get<HTMLButtonElement>('save');
const status = get<HTMLParagraphElement>('edit-status');
const headers = {Authorization: 'Bearer alice-local-token'};

function bookmark(value: unknown): Bookmark {
  const x = value as Partial<Bookmark> | null;
  if (!x || typeof x.id !== 'string' || typeof x.title !== 'string' || typeof x.url !== 'string' ||
      !Number.isSafeInteger(x.version) || Number(x.version) < 1 || !Number.isSafeInteger(x.created_at)) {
    throw new Error('Invalid bookmark response');
  }
  return x as Bookmark;
}
function page(value: unknown): Page {
  const x = value as Partial<Page> | null;
  if (!x || !Array.isArray(x.items) || (x.nextCursor !== null && typeof x.nextCursor !== 'string')) {
    throw new Error('Invalid list response');
  }
  return {items: x.items.map(bookmark), nextCursor: x.nextCursor};
}

let confirmed: Bookmark | null = null;
let draft = '';
let revision = 0;
let generation = 0; // changes on select/dispose; server versions are a separate ordering
let pending: Pending | null = null;
let saving = false;
let conflict = false;
let editorController: AbortController | null = null;
let opener: HTMLButtonElement | null = null;

function paintEditor(message?: string): void {
  get('editor').hidden = confirmed === null;
  if (!confirmed) return;
  title.value = draft;
  get('confirmed').textContent = `Server: ${confirmed.title} · version ${confirmed.version}`;
  save.disabled = saving || conflict || !draft.trim() || (!pending && draft === confirmed.title);
  save.textContent = saving ? 'Saving…' : pending ? 'Retry save' : 'Save title';
  get('resolve').hidden = !conflict;
  if (message !== undefined) status.textContent = message;
}

function openEditor(row: Bookmark, source: HTMLButtonElement): void {
  editorController?.abort();
  editorController = new AbortController();
  generation++;
  confirmed = row;
  draft = row.title;
  revision = 0;
  pending = null;
  saving = false;
  conflict = false;
  opener = source;
  paintEditor('Ready to edit.');
  title.focus();
}

function closeEditor(): void {
  generation++;
  editorController?.abort();
  confirmed = null;
  pending = null;
  saving = false;
  paintEditor();
  if (opener?.isConnected) opener.focus();
  else get('search').focus();
}

title.addEventListener('input', () => {
  draft = title.value;
  revision++;
  paintEditor(conflict ? 'Conflict. Your draft is retained. Choose the server version before saving.' :
              saving ? 'Saving the earlier edit. Your newer draft is retained.' : 'Unsaved changes.');
});

get('edit-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!confirmed || saving || conflict || !draft.trim()) return;
  // Retrying an uncertain result reuses A's exact payload and key, even after B is typed.
  pending ??= {key: crypto.randomUUID(), title: draft, revision, expectedVersion: confirmed.version, generation};
  const mutation = pending;
  const id = confirmed.id;
  saving = true;
  paintEditor('Saving…');
  try {
    const response = await fetch(`/api/bookmarks/${encodeURIComponent(id)}`, {
      method: 'PATCH', signal: editorController?.signal,
      headers: {...headers, 'Content-Type': 'application/json', 'Idempotency-Key': mutation.key},
      body: JSON.stringify({title: mutation.title, expectedVersion: mutation.expectedVersion})
    });
    const body: unknown = await response.json();
    if (generation !== mutation.generation || pending?.key !== mutation.key || !confirmed) return;
    if (response.status === 409) {
      const current = bookmark((body as {current: unknown}).current);
      if (current.id !== id) throw new Error('Mismatched bookmark response');
      if (current.version >= confirmed.version) confirmed = current;
      pending = null;
      saving = false;
      conflict = true;
      paintEditor('Conflict. Your draft is retained. Review the server copy, then keep your draft.');
      get('resolve').focus();
      return;
    }
    if (!response.ok) throw new Error(`Save failed (${response.status}).`);
    const current = bookmark(body);
    if (current.id !== id) throw new Error('Mismatched bookmark response');
    if (current.version >= confirmed.version) confirmed = current;
    if (revision === mutation.revision) draft = confirmed.title;
    pending = null;
    saving = false;
    paintEditor(draft === confirmed.title ? 'Saved.' : 'Earlier edit saved. Your newer draft is unsaved.');
  } catch (error) {
    if (generation !== mutation.generation || !confirmed) return;
    saving = false;
    paintEditor('Save outcome unavailable. Your draft is retained. Retry uses the same mutation.');
  }
});

get('resolve').addEventListener('click', () => {
  conflict = false;
  paintEditor('Draft retained. Save will use the displayed server version.');
  title.focus();
});
get('close').addEventListener('click', closeEditor);
get('refresh').addEventListener('click', async () => {
  if (!confirmed) return;
  const mine = generation, id = confirmed.id;
  try {
    const response = await fetch(`/api/bookmarks/${encodeURIComponent(id)}`, {headers, signal: editorController?.signal});
    if (!response.ok) throw new Error('Refresh failed');
    const current = bookmark(await response.json());
    if (mine !== generation || !confirmed || current.id !== id) return;
    const dirty = draft !== confirmed.title;
    if (current.version > confirmed.version) {
      confirmed = current;
      if (!dirty && !pending) draft = current.title;
      paintEditor('Server copy refreshed. Unsaved edits are retained.');
    } else {
      paintEditor('Server copy unchanged. Unsaved edits are retained.');
    }
  } catch {
    if (mine === generation && confirmed) paintEditor('Refresh failed. Your draft is retained; try Refresh again.');
  }
});

let searchGeneration = 0;
let listController: AbortController | null = null;
let nextCursor: string | null = null;
let currentQuery = '';
let rows: Bookmark[] = [];
let failedAppend = false;
async function search(append = false): Promise<void> {
  listController?.abort();
  listController = new AbortController();
  const mine = ++searchGeneration;
  if (!append) {
    currentQuery = get<HTMLInputElement>('search').value;
    // Rows and their cursor belong to one query. A failed new search must never
    // leave an old continuation usable with the new query.
    rows = [];
    nextCursor = null;
    get('results').replaceChildren();
    get('more').hidden = true;
  }
  const params = new URLSearchParams({q: currentQuery, limit: '2'});
  if (append && nextCursor) params.set('cursor', nextCursor);
  get('list-status').textContent = 'Loading…';
  get('retry-list').hidden = true;
  get<HTMLButtonElement>('more').disabled = true;
  try {
    const response = await fetch(`/api/bookmarks?${params}`, {headers, signal: listController.signal});
    if (!response.ok) throw new Error(`Search failed (${response.status})`);
    const data = page(await response.json());
    if (mine !== searchGeneration) return;
    const combined = append ? [...rows, ...data.items] : data.items;
    rows = Array.from(new Map(combined.map(row => [row.id, row])).values());
    nextCursor = data.nextCursor;
    const list = get('results');
    list.replaceChildren();
    for (const row of rows) {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.textContent = `Edit ${row.title}`;
      button.addEventListener('click', () => openEditor(row, button));
      item.append(button);
      list.append(item);
    }
    get('list-status').textContent = rows.length ? `${rows.length} bookmarks loaded.` : 'No bookmarks found.';
    get('more').hidden = nextCursor === null;
  } catch {
    if (mine !== searchGeneration) return;
    failedAppend = append;
    get('list-status').textContent = 'Search failed. Retry to load bookmarks.';
    get('retry-list').hidden = false;
  } finally {
    if (mine === searchGeneration) get<HTMLButtonElement>('more').disabled = false;
  }
}
get('search-form').addEventListener('submit', event => {event.preventDefault(); void search();});
get('more').addEventListener('click', () => {void search(true);});
get('retry-list').addEventListener('click', () => {void search(failedAppend);});
window.addEventListener('pagehide', () => {generation++; searchGeneration++; editorController?.abort(); listController?.abort();});
void search();
