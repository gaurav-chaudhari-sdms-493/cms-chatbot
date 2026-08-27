import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AgentQueryResponse } from '../types';

interface Props {
  data: AgentQueryResponse;
}

export const MarkdownReport: React.FC<Props> = ({ data }) => {
  return (
    <div className="agent-markdown-body" style={{ color: 'var(--text-primary)', lineHeight: 1.7, fontSize: '15px', padding: '8px 0' }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {data.markdown_report}
      </ReactMarkdown>
    </div>
  );
};
