import Icon from "./Icon.jsx";

export default function TranslationPane({ blocks, selectedBlockId, setSelectedBlockId, autoTranslate }) {
  return (
    <section className="reader-pane translation-pane" aria-label="翻译">
      <div className="pane-header">
        <div>
          <span>翻译</span>
          <strong>{autoTranslate ? "自动翻译 ON" : "手动翻译"}</strong>
        </div>
        <button type="button" className="pane-tool">
          <Icon name="translate" />
          重新翻译本页
        </button>
      </div>

      <div className="translation-list">
        {blocks.map((block, index) => (
          <article
            key={block.id}
            className={`translation-block ${block.id === selectedBlockId ? "is-selected" : ""}`}
            onClick={() => setSelectedBlockId(block.id)}
          >
            <div className="block-index">{String(index + 1).padStart(2, "0")}</div>
            <p>{block.translation}</p>
            <div className="block-meta">
              <span>{block.kind}</span>
              <span>{block.id}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
