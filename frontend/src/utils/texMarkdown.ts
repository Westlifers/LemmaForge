import MarkdownIt from "markdown-it";
import katex from "katex";

const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

interface TexPlaceholder {
  marker: string;
  html: string;
  displayMode: boolean;
}

const environmentMap: Record<string, string | null> = {
  equation: null,
  "equation*": null,
  align: "aligned",
  "align*": "aligned",
  gather: "gathered",
  "gather*": "gathered",
  multline: "gathered",
  "multline*": "gathered",
  aligned: "aligned",
  gathered: "gathered",
  cases: "cases",
  matrix: "matrix",
  pmatrix: "pmatrix",
  bmatrix: "bmatrix",
  vmatrix: "vmatrix",
  Vmatrix: "Vmatrix"
};

export function renderMarkdownWithTex(source: string): string {
  const { markdown, placeholders } = extractTex(source || "");
  let html = md.render(markdown);

  placeholders.forEach((placeholder) => {
    const paragraphPattern = new RegExp(
      `<p>\\s*${escapeRegExp(placeholder.marker)}\\s*</p>`,
      "g"
    );
    if (placeholder.displayMode) {
      html = html.replace(paragraphPattern, placeholder.html);
    }
    html = html.replaceAll(placeholder.marker, placeholder.html);
  });

  return html;
}

function extractTex(source: string) {
  const placeholders: TexPlaceholder[] = [];
  let markdown = "";
  let index = 0;

  function addPlaceholder(expression: string, displayMode: boolean, environment?: string) {
    const marker = `LEMMAFORGE_TEX_${placeholders.length}_END`;
    const normalized = normalizeEnvironment(expression, environment);
    placeholders.push({
      marker,
      displayMode,
      html: katex.renderToString(normalized.trim(), {
        displayMode,
        throwOnError: false,
        trust: false
      })
    });
    return displayMode ? `\n\n${marker}\n\n` : marker;
  }

  while (index < source.length) {
    const fenceEnd = fencedCodeEnd(source, index);
    if (fenceEnd !== null) {
      markdown += source.slice(index, fenceEnd);
      index = fenceEnd;
      continue;
    }

    if (source[index] === "`") {
      const codeEnd = inlineCodeEnd(source, index);
      if (codeEnd !== null) {
        markdown += source.slice(index, codeEnd);
        index = codeEnd;
        continue;
      }
    }

    if (source.startsWith("$$", index)) {
      const end = findClosingDelimiter(source, index + 2, "$$", true);
      if (end !== null) {
        markdown += addPlaceholder(source.slice(index + 2, end), true);
        index = end + 2;
        continue;
      }
    }

    if (source.startsWith("\\[", index)) {
      const end = findClosingDelimiter(source, index + 2, "\\]", true);
      if (end !== null) {
        markdown += addPlaceholder(source.slice(index + 2, end), true);
        index = end + 2;
        continue;
      }
    }

    if (source.startsWith("\\(", index)) {
      const end = findClosingDelimiter(source, index + 2, "\\)", false);
      if (end !== null) {
        markdown += addPlaceholder(source.slice(index + 2, end), false);
        index = end + 2;
        continue;
      }
    }

    const environment = texEnvironmentAt(source, index);
    if (environment) {
      const endMarker = `\\end{${environment.name}}`;
      const end = source.indexOf(endMarker, environment.bodyStart);
      if (end >= 0) {
        markdown += addPlaceholder(
          source.slice(index, end + endMarker.length),
          true,
          environment.name
        );
        index = end + endMarker.length;
        continue;
      }
    }

    if (source[index] === "$" && source[index + 1] !== "$" && source[index + 1]?.trim()) {
      const end = findClosingDollar(source, index + 1);
      if (end !== null) {
        const expression = source.slice(index + 1, end);
        if (expression.trim() && !/\s$/.test(expression)) {
          markdown += addPlaceholder(expression, false);
          index = end + 1;
          continue;
        }
      }
    }

    markdown += source[index];
    index += 1;
  }

  return { markdown, placeholders };
}

function fencedCodeEnd(source: string, index: number): number | null {
  if (index > 0 && source[index - 1] !== "\n") return null;
  const match = /^( {0,3})(`{3,}|~{3,})/.exec(source.slice(index));
  if (!match) return null;

  const fence = match[2];
  const fenceChar = fence[0];
  const fenceLength = fence.length;
  let cursor = source.indexOf("\n", index);
  if (cursor < 0) return source.length;
  cursor += 1;

  while (cursor < source.length) {
    const lineEnd = source.indexOf("\n", cursor);
    const end = lineEnd < 0 ? source.length : lineEnd + 1;
    const line = source.slice(cursor, lineEnd < 0 ? source.length : lineEnd);
    const closing = new RegExp(`^ {0,3}${escapeRegExp(fenceChar)}{${fenceLength},}\\s*$`);
    if (closing.test(line)) return end;
    cursor = end;
  }

  return source.length;
}

function inlineCodeEnd(source: string, index: number): number | null {
  const match = /^`+/.exec(source.slice(index));
  if (!match) return null;
  const marker = match[0];
  const end = source.indexOf(marker, index + marker.length);
  return end >= 0 ? end + marker.length : null;
}

function findClosingDelimiter(
  source: string,
  start: number,
  delimiter: string,
  allowNewline: boolean
): number | null {
  let cursor = start;
  while (cursor < source.length) {
    if (!allowNewline && source[cursor] === "\n") return null;
    if (source.startsWith(delimiter, cursor) && !isEscaped(source, cursor)) return cursor;
    cursor += 1;
  }
  return null;
}

function findClosingDollar(source: string, start: number): number | null {
  let cursor = start;
  while (cursor < source.length) {
    if (source[cursor] === "\n") return null;
    if (source[cursor] === "$" && !isEscaped(source, cursor)) return cursor;
    cursor += 1;
  }
  return null;
}

function texEnvironmentAt(source: string, index: number) {
  const names = Object.keys(environmentMap)
    .map(escapeRegExp)
    .join("|");
  const match = new RegExp(`^\\\\begin\\{(${names})\\}`).exec(source.slice(index));
  if (!match) return null;
  return {
    name: match[1],
    bodyStart: index + match[0].length
  };
}

function normalizeEnvironment(expression: string, environment?: string): string {
  if (!environment) return expression;
  const displayEnvironment = environmentMap[environment];
  const begin = `\\begin{${environment}}`;
  const end = `\\end{${environment}}`;
  const body = expression.slice(begin.length, expression.length - end.length).trim();

  if (displayEnvironment === null) return body;
  if (displayEnvironment === environment) return expression;
  return `\\begin{${displayEnvironment}}\n${body}\n\\end{${displayEnvironment}}`;
}

function isEscaped(source: string, index: number): boolean {
  let slashCount = 0;
  let cursor = index - 1;
  while (cursor >= 0 && source[cursor] === "\\") {
    slashCount += 1;
    cursor -= 1;
  }
  return slashCount % 2 === 1;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
