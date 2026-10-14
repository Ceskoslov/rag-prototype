import type { AgentTrace } from '@/types/chat'

interface AgentTracePanelProps {
  trace: AgentTrace | null
}

const labelFor = (value = 'unknown') =>
  value
    .split(/[_-]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

export const AgentTracePanel = ({ trace }: AgentTracePanelProps) => {
  if (!trace) return null

  return (
    <aside className="w-96 border-l border-gray-200 p-4 overflow-y-auto bg-gray-50">
      <h2 className="text-lg font-semibold text-gray-900">RAG trace</h2>
      <p className="text-sm text-gray-600 mb-4">Retrieval evidence and pipeline steps</p>

      <section className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <h3 className="font-medium text-gray-900 mb-2">Knowledge bases searched</h3>
        <div className="flex flex-wrap gap-2">
          {(trace.knowledge_bases_searched ?? []).map((name) => (
            <span
              key={name}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {labelFor(name)}
            </span>
          ))}
        </div>
        <dl className="mt-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-600">Iterations</dt>
            <dd className="font-medium">{trace.iterations}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Steps</dt>
            <dd className="font-medium">{(trace.pipeline_steps ?? []).join(' → ')}</dd>
          </div>
          {trace.metrics?.elapsed_ms !== undefined && <div className="flex justify-between"><dt>Total time</dt><dd>{(trace.metrics.elapsed_ms / 1000).toFixed(2)} s</dd></div>}
          {trace.metrics?.first_token_ms != null && <div className="flex justify-between"><dt>First token</dt><dd>{(trace.metrics.first_token_ms / 1000).toFixed(2)} s</dd></div>}
          {trace.metrics?.tokens?.total_tokens !== undefined && <div className="flex justify-between"><dt>Reported tokens</dt><dd>{trace.metrics.tokens.total_tokens}</dd></div>}
        </dl>
        {trace.metrics?.stages && <ol className="mt-3 text-xs">{trace.metrics.stages.map((stage, index) => <li key={index}>{stage.stage}: {Math.round(stage.duration_ms)} ms</li>)}</ol>}
      </section>

      {(trace.retrieval_sources ?? []).length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="font-medium text-gray-900 mb-3">
            Sources ({trace.retrieval_sources.length})
          </h3>
          <div className="space-y-3">
            {trace.retrieval_sources.map((source, index) => (
              <article key={`${source.title}-${index}`} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold text-gray-900">{source.title}</h4>
                  <span className="text-xs text-blue-700">
                    {labelFor(source.knowledge_base)}
                  </span>
                </div>
                {source.snippet && (
                  <p className="text-xs text-gray-600 mt-2 line-clamp-3">{source.snippet}</p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}
    </aside>
  )
}
