import Icon from "./Icon.jsx";

export default function TopToolbar({
  document,
  zoom,
  setZoom,
  autoTranslate,
  setAutoTranslate,
  syncScroll,
  setSyncScroll,
  onSave,
}) {
  return (
    <header className="top-toolbar">
      <div className="brand-block">
        <div className="brand-mark">LW</div>
        <div>
          <h1>LLM Wiki Reader</h1>
          <p>{document.title}</p>
        </div>
      </div>

      <div className="toolbar-cluster page-control" aria-label="页码控制">
        <button type="button" aria-label="上一页">
          -
        </button>
        <strong>
          {document.currentPage} / {document.totalPages}
        </strong>
        <button type="button" aria-label="下一页">
          +
        </button>
      </div>

      <div className="toolbar-cluster">
        <button type="button" onClick={() => setZoom(Math.max(80, zoom - 10))}>
          -
        </button>
        <span>{zoom}%</span>
        <button type="button" onClick={() => setZoom(Math.min(140, zoom + 10))}>
          +
        </button>
      </div>

      <label className={`toggle ${autoTranslate ? "is-on" : ""}`}>
        <input
          type="checkbox"
          checked={autoTranslate}
          onChange={(event) => setAutoTranslate(event.target.checked)}
        />
        <Icon name="translate" />
        自动翻译
      </label>

      <label className={`toggle ${syncScroll ? "is-on" : ""}`}>
        <input
          type="checkbox"
          checked={syncScroll}
          onChange={(event) => setSyncScroll(event.target.checked)}
        />
        <Icon name="sync" />
        同步滚动
      </label>

      <button className="primary-action" type="button" onClick={onSave}>
        <Icon name="save" />
        保存到知识库
      </button>
    </header>
  );
}
