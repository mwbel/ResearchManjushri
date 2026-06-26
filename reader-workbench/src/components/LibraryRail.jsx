import { readingQueue } from "../data/demoDocument.js";
import Icon from "./Icon.jsx";

export default function LibraryRail({ activeId, log }) {
  return (
    <aside className="library-rail">
      <div className="rail-section">
        <div className="rail-title">
          <Icon name="library" />
          <span>阅读队列</span>
        </div>
        <div className="queue-list">
          {readingQueue.map((item) => (
            <button
              className={`queue-item ${item.id === activeId ? "is-active" : ""}`}
              type="button"
              key={item.id}
            >
              <strong>{item.title}</strong>
              <span>{item.domain}</span>
              <small>{item.progress}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="rail-section">
        <div className="rail-title">
          <Icon name="note" />
          <span>集成事件</span>
        </div>
        <div className="event-log">
          {log.map((item) => (
            <p key={item.id}>{item.text}</p>
          ))}
        </div>
      </div>
    </aside>
  );
}
