import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import { Tag } from 'antd';
import 'highlight.js/styles/github.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className,
}) => {
  return (
    <div className={`markdown-body ${className || ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // 自定义引用标签 [来源X] 的渲染
          p: ({ children }) => {
            const text = String(children);
            // 将 [来源X] 替换为可点击的Tag
            const parts = text.split(/(\[(?:来源|cite)\d+\])/g);
            return (
              <p>
                {parts.map((part, i) => {
                  const match = part.match(/\[(?:来源|cite)(\d+)\]/);
                  if (match) {
                    return (
                      <Tag
                        key={i}
                        color="blue"
                        className="cursor-pointer mx-1"
                        onClick={() => {
                          // 滚动到引用面板对应位置
                          const element = document.getElementById(
                            `citation-${match[1]}`
                          );
                          element?.scrollIntoView({ behavior: 'smooth' });
                        }}
                      >
                        📎 来源{match[1]}
                      </Tag>
                    );
                  }
                  return part;
                })}
              </p>
            );
          },
          // 代码块
          code: ({ className: codeClassName, children, ...props }) => {
            const isInline = !codeClassName;
            if (isInline) {
              return (
                <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
          // 表格
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="border-collapse border border-gray-300 w-full text-sm">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-gray-300 bg-gray-50 px-3 py-2 text-left">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-gray-300 px-3 py-2">{children}</td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
