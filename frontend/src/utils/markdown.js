import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Plain textarea input - a single newline should still break the line,
// which isn't CommonMark's default (it normally needs a blank line).
marked.setOptions({ breaks: true });

export function renderMarkdown(text) {
  if (!text) return '';
  return DOMPurify.sanitize(marked.parse(text));
}
