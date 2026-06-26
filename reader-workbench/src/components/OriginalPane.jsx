import Icon from "./Icon.jsx";

export default function OriginalPane({ blocks, selectedBlockId, setSelectedBlockId, zoom, query, setQuery }) {
  return (
    <section className="reader-pane original-pane" aria-label="原文">
      <div className="pane-header">
        <div>
          <span>原文</span>
          <strong>PDF page 12</strong>
        </div>
        <label className="search-box">
          <Icon name="search" size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索原文" />
        </label>
      </div>

      <div className="page-canvas" style={{ "--page-zoom": zoom / 100 }}>
        <div className="page-sheet">
          <div className="page-running-head">SAMPLE EDITION · The Human-Agent Orchestrator</div>
          <h2>The Human-Agent Orchestrator</h2>
          {blocks.map((block) => {
            const isSelected = block.id === selectedBlockId;
            const isMatch = query && block.original.toLowerCase().includes(query.toLowerCase());
            return (
              <button
                key={block.id}
                type="button"
                className={`original-block ${isSelected ? "is-selected" : ""} ${isMatch ? "is-match" : ""}`}
                onClick={() => setSelectedBlockId(block.id)}
              >
                {block.original}
              </button>
            );
          })}
          <div className="page-footer">-- The Authors</div>
        </div>
      </div>
    </section>
  );
}
