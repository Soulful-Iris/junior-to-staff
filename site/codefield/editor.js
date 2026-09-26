// The editor: CodeMirror 6, Python, the guide's colours.
//
// What it adds to a plain CodeMirror, and why:
//   breakpoints   a gutter dot per line; they move with the text as it is edited
//   given lines   the problem's own data classes cannot be edited, because the
//                 tests depend on their exact shape (a transaction filter, so
//                 Reset can still replace them)
//   line marks    the loop a run was stopped in, the line an error came from,
//                 the breakpoint stop being looked at
import { EditorState, StateField, StateEffect, RangeSet, Annotation, Prec } from "@codemirror/state";
import {
  EditorView, keymap, lineNumbers, gutter, GutterMarker, highlightActiveLine,
  highlightActiveLineGutter, drawSelection, Decoration, WidgetType,
} from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { indentUnit, bracketMatching, syntaxHighlighting, HighlightStyle, indentOnInput } from "@codemirror/language";
import { python } from "@codemirror/lang-python";
import { closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { tags as t } from "@lezer/highlight";

// ---------------------------------------------------------------- breakpoints
const bpEffect = StateEffect.define({ map: (v, m) => ({ pos: m.mapPos(v.pos), on: v.on }) });
const bpClear = StateEffect.define();
const bpMarker = new (class extends GutterMarker {
  toDOM() { const s = document.createElement("span"); s.className = "cf-bp"; return s; }
})();
const bpState = StateField.define({
  create: () => RangeSet.empty,
  update(set, tr) {
    set = set.map(tr.changes);
    for (const e of tr.effects) {
      if (e.is(bpClear)) set = RangeSet.empty;
      if (e.is(bpEffect)) {
        set = e.value.on
          ? set.update({ add: [bpMarker.range(e.value.pos)] })
          : set.update({ filter: (from) => from !== e.value.pos });
      }
    }
    return set;
  },
});

function toggleBreakpoint(view, pos) {
  let has = false;
  view.state.field(bpState).between(pos, pos, () => { has = true; });
  view.dispatch({ effects: bpEffect.of({ pos, on: !has }) });
}

// ---------------------------------------------------------------- given lines
const givenSet = StateEffect.define();
const givenState = StateField.define({
  create: () => Decoration.none,
  update(deco, tr) {
    deco = deco.map(tr.changes);
    for (const e of tr.effects) if (e.is(givenSet)) deco = e.value;
    return deco;
  },
  provide: (f) => EditorView.decorations.from(f),
});
const givenLine = Decoration.line({ class: "cf-given" });

function givenDecorations(doc, ranges) {
  const items = [];
  ranges.forEach(([first, last], i) => {
    for (let n = first; n <= Math.min(last, doc.lines); n++) {
      const line = doc.line(n);
      items.push(givenLine.range(line.from));
      if (i === 0 && n === first) items.push(Decoration.widget({ widget: new GivenTag(), side: 1 }).range(line.to));
    }
  });
  return Decoration.set(items, true);
}

// Replacing the whole text (Reset) is the one change allowed to touch them.
const allowAll = Annotation.define();

// A transaction that touches a given line, anywhere, is dropped. The reader
// types on the lines after; Python does not mind imports added lower down.
// Replacing the WHOLE text is always allowed (select all, paste your file):
// the protection drops, and the page puts it back if the given lines are
// still there verbatim afterwards.
const protectGiven = EditorState.transactionFilter.of((tr) => {
  if (!tr.docChanged || tr.annotation(allowAll)) return tr;
  const deco = tr.startState.field(givenState);
  const doc = tr.startState.doc;
  let whole = false;
  tr.changes.iterChangedRanges((fromA, toA) => { if (fromA === 0 && toA === doc.length) whole = true; });
  if (whole) return [tr, { effects: givenSet.of(Decoration.none) }];
  let blocked = false;
  tr.changes.iterChangedRanges((fromA, toA) => {
    deco.between(0, doc.length, (from) => {
      const line = doc.lineAt(from);
      if (fromA <= line.to && toA >= line.from) blocked = true;
    });
  });
  return blocked ? [] : tr;
});

class GivenTag extends WidgetType {
  toDOM() {
    const s = document.createElement("span");
    s.className = "cf-given-tag";
    s.textContent = "given, read-only";
    return s;
  }
}

// ----------------------------------------------------------------- line marks
const marksSet = StateEffect.define();
const marksState = StateField.define({
  create: () => Decoration.none,
  update(deco, tr) {
    if (tr.docChanged) deco = Decoration.none;          // stale the moment the code moves
    for (const e of tr.effects) if (e.is(marksSet)) deco = e.value;
    return deco;
  },
  provide: (f) => EditorView.decorations.from(f),
});

class TagWidget extends WidgetType {
  constructor(text, kind) { super(); this.text = text; this.kind = kind; }
  eq(o) { return o.text === this.text && o.kind === this.kind; }
  toDOM() {
    const s = document.createElement("span");
    s.className = `cf-line-tag cf-line-tag-${this.kind}`;
    s.textContent = this.text;
    return s;
  }
}

// ---------------------------------------------------------------------- look
const theme = EditorView.theme({
  "&": { backgroundColor: "#202e28", color: "#e6eee0", fontSize: "13px" },
  ".cm-content": { fontFamily: "var(--cf-mono)", padding: "14px 0", caretColor: "#cfe1b3" },
  ".cm-scroller": { fontFamily: "var(--cf-mono)", lineHeight: "23px" },
  ".cm-gutters": { backgroundColor: "#202e28", color: "#5f7367", border: "none" },
  ".cm-lineNumbers .cm-gutterElement": { padding: "0 14px 0 6px", fontSize: "12px" },
  ".cm-activeLine": { backgroundColor: "#26362f" },
  ".cm-activeLineGutter": { backgroundColor: "#26362f", color: "#b5c999" },
  "&.cm-focused .cm-cursor": { borderLeftColor: "#cfe1b3", borderLeftWidth: "2px" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": { backgroundColor: "#3d5a4b !important" },
  ".cm-matchingBracket": { backgroundColor: "#35503f", outline: "1px solid #6f8f76" },
  "&.cm-focused": { outline: "none" },
}, { dark: true });

const highlight = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.operatorKeyword, t.definitionKeyword, t.moduleKeyword], color: "#b5c999" },
  { tag: [t.string, t.special(t.string)], color: "#e5cc9c" },
  { tag: [t.number, t.bool, t.null], color: "#e2b77f" },
  { tag: t.comment, color: "#7f9585", fontStyle: "italic" },
  { tag: [t.function(t.definition(t.variableName)), t.definition(t.className)], color: "#f4f7ee", fontWeight: "700" },
  { tag: [t.standard(t.variableName), t.meta], color: "#9ec6b2" },
  { tag: [t.operator, t.punctuation, t.bracket], color: "#aab9a7" },
  { tag: t.self, color: "#d6c9e8" },
]);

// ----------------------------------------------------------------------- api
export function createEditor(parent, { doc, given = [], onRun, onChange, breakpoints = [] }) {
  const extensions = [
    lineNumbers(),
    gutter({
      class: "cf-bp-gutter",
      markers: (v) => v.state.field(bpState),
      initialSpacer: () => bpMarker,
      renderEmptyElements: true,      // every line clickable, and the hover dot has somewhere to be
      domEventHandlers: {
        mousedown(view, line) { toggleBreakpoint(view, line.from); return true; },
      },
    }),
    bpState, givenState, marksState, protectGiven,
    highlightActiveLine(), highlightActiveLineGutter(), drawSelection(),
    history(), indentOnInput(), bracketMatching(), closeBrackets(),
    indentUnit.of("    "), EditorState.tabSize.of(4),
    python(), syntaxHighlighting(highlight), theme,
    Prec.highest(keymap.of([
      { key: "Mod-Enter", run: () => { onRun && onRun(); return true; } },
      { key: "Shift-Enter", run: () => { onRun && onRun(); return true; } },
    ])),
    keymap.of([...closeBracketsKeymap, ...defaultKeymap, ...historyKeymap, indentWithTab]),
    EditorView.updateListener.of((u) => { if (u.docChanged && onChange) onChange(); }),
    EditorView.contentAttributes.of({ "aria-label": "Your solution, Python" }),
  ];
  const view = new EditorView({ parent, state: EditorState.create({ doc, extensions }) });

  function applyGiven(ranges) {
    view.dispatch({ effects: givenSet.of(givenDecorations(view.state.doc, ranges)) });
  }
  function setBreakpoints(lines) {
    const effects = [bpClear.of(null)];
    for (const n of lines) if (n >= 1 && n <= view.state.doc.lines) effects.push(bpEffect.of({ pos: view.state.doc.line(n).from, on: true }));
    view.dispatch({ effects });
  }
  applyGiven(given);
  setBreakpoints(breakpoints);

  return {
    view,
    getCode: () => view.state.doc.toString(),
    setCode(code, ranges = []) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: code }, annotations: allowAll.of(true) });
      applyGiven(ranges);
    },
    getBreakpoints() {
      const out = [];
      view.state.field(bpState).between(0, view.state.doc.length, (from) => { out.push(view.state.doc.lineAt(from).number); });
      return [...new Set(out)].sort((a, b) => a - b);
    },
    setBreakpoints,
    setGiven: applyGiven,
    hasGiven: () => view.state.field(givenState).size > 0,
    // marks: [{from, to, kind: 'stop'|'error'|'here', tag?}]
    mark(marks) {
      const doc = view.state.doc;
      const items = [];
      for (const m of marks) {
        for (let n = Math.max(1, m.from); n <= Math.min(m.to, doc.lines); n++) {
          const line = doc.line(n);
          items.push(Decoration.line({ class: `cf-line-${m.kind}` }).range(line.from));
          if (m.tag && n === m.from) items.push(Decoration.widget({ widget: new TagWidget(m.tag, m.kind), side: 1 }).range(line.to));
        }
      }
      view.dispatch({ effects: marksSet.of(Decoration.set(items, true)) });
    },
    clearMarks() { view.dispatch({ effects: marksSet.of(Decoration.none) }); },
    revealLine(n) {
      if (n < 1 || n > view.state.doc.lines) return;
      view.dispatch({ effects: EditorView.scrollIntoView(view.state.doc.line(n).from, { y: "nearest" }) });
    },
    focus: () => view.focus(),
  };
}

// A reader's own input: a few lines of setup and the call to run on the last.
// Same colours and keys as the main editor, no gutter: it is a cell, not a file.
export function createCellEditor(parent, { doc, onRun, onChange, label }) {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        history(), indentOnInput(), bracketMatching(), closeBrackets(),
        indentUnit.of("    "), EditorState.tabSize.of(4),
        python(), syntaxHighlighting(highlight), theme, drawSelection(),
        EditorView.theme({ ".cm-content": { padding: "9px 0" }, ".cm-line": { padding: "0 12px" } }),
        Prec.highest(keymap.of([
          { key: "Mod-Enter", run: () => { onRun && onRun(); return true; } },
          { key: "Shift-Enter", run: () => { onRun && onRun(); return true; } },
        ])),
        keymap.of([...closeBracketsKeymap, ...defaultKeymap, ...historyKeymap, indentWithTab]),
        EditorView.updateListener.of((u) => { if (u.docChanged && onChange) onChange(); }),
        EditorView.contentAttributes.of({ "aria-label": label || "Your input, Python" }),
      ],
    }),
  });
  return {
    view,
    getCode: () => view.state.doc.toString(),
    focus() { view.focus(); view.dispatch({ selection: { anchor: view.state.doc.length } }); },
    destroy: () => view.destroy(),
  };
}

