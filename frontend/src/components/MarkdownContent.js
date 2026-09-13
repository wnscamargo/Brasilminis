import Markdown from "react-markdown";

// Renderiza Markdown de forma SEGURA (sem HTML bruto — react-markdown não habilita rehype-raw).
// Estilização controlada via mapa de componentes (títulos, parágrafos, negrito, listas, links).
const components = {
  h1: (p) => <h2 className="text-2xl font-display font-black uppercase text-white mt-8 mb-3" {...p} />,
  h2: (p) => <h2 className="text-xl font-display font-bold uppercase text-white mt-7 mb-3" {...p} />,
  h3: (p) => <h3 className="text-lg font-display font-bold text-white mt-5 mb-2" {...p} />,
  h4: (p) => <h4 className="text-base font-semibold text-white mt-4 mb-2" {...p} />,
  p: (p) => <p className="text-gray-300 leading-relaxed mb-4" {...p} />,
  strong: (p) => <strong className="text-white font-bold" {...p} />,
  em: (p) => <em className="italic" {...p} />,
  ul: (p) => <ul className="list-disc pl-6 space-y-1.5 text-gray-300 mb-4" {...p} />,
  ol: (p) => <ol className="list-decimal pl-6 space-y-1.5 text-gray-300 mb-4" {...p} />,
  li: (p) => <li className="leading-relaxed" {...p} />,
  a: ({ href, ...rest }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#FFC107] underline hover:text-[#e0a800]" {...rest} />
  ),
  blockquote: (p) => <blockquote className="border-l-2 border-[#FFC107] pl-4 italic text-gray-400 my-4" {...p} />,
  code: (p) => <code className="bg-[#111] px-1.5 py-0.5 rounded text-[#FFC107] text-sm" {...p} />,
};

export default function MarkdownContent({ children, ...props }) {
  return (
    <div data-testid="markdown-content" {...props}>
      <Markdown components={components} skipHtml>{children || ""}</Markdown>
    </div>
  );
}
