import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false, // 不渲染原始 HTML，防注入
  breaks: true, // 换行转 <br>
  linkify: true,
})

export function renderMarkdown(text: string): string {
  return md.render(text || '')
}
