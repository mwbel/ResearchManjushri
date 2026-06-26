import { useMemo, useState } from "react";
import Icon from "./Icon.jsx";

const tabs = ["摘要", "解释", "笔记", "概念"];

export default function AISidebar({ document, selectedBlock, notes, setNotes, onExplain, onSave }) {
  const [activeTab, setActiveTab] = useState("解释");
  const [draftNote, setDraftNote] = useState("");
  const [question, setQuestion] = useState("这段和 AI 编排有什么关系？");

  const conceptList = useMemo(() => {
    const map = new Map();
    document.page.blocks.forEach((block) => {
      block.concepts.forEach((concept) => map.set(concept, (map.get(concept) || 0) + 1));
    });
    return Array.from(map.entries()).map(([label, count]) => ({ label, count }));
  }, [document]);

  function addNote() {
    if (!draftNote.trim()) return;
    setNotes((current) => [
      {
        id: crypto.randomUUID(),
        blockId: selectedBlock.id,
        text: draftNote.trim(),
      },
      ...current,
    ]);
    setDraftNote("");
  }

  return (
    <aside className="ai-sidebar" aria-label="AI 解释">
      <div className="pane-header sidebar-header">
        <div>
          <span>AI 解释</span>
          <strong>page {document.currentPage}</strong>
        </div>
        <button className="pane-tool" type="button" onClick={onExplain}>
          <Icon name="spark" />
          生成解释
        </button>
      </div>

      <div className="tab-strip">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={tab === activeTab ? "is-active" : ""}
            type="button"
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "摘要" && (
        <section className="sidebar-section">
          <h2>本页摘要</h2>
          <p>
            本页把《The Human-Agent Orchestrator》定位为一本从 agent 技术理解转向组织领导与风险控制的书。作者强调，真正的问题不只是部署 agent，而是如何持续、负责任地领导它们。
          </p>
          <div className="reference-list">
            <span>证据引用</span>
            <button type="button">p12-b1</button>
            <button type="button">p12-b4</button>
          </div>
        </section>
      )}

      {activeTab === "解释" && (
        <section className="sidebar-section">
          <h2>选中段落</h2>
          <blockquote>{selectedBlock.original}</blockquote>
          <div className="answer-card">
            <strong>解释</strong>
            <p>{selectedBlock.explanation}</p>
            <div className="reference-list">
              <span>证据引用</span>
              <button type="button">{selectedBlock.id}</button>
            </div>
          </div>
          <label className="question-box">
            <span>继续提问</span>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} />
          </label>
          <button className="primary-action full-width" type="button" onClick={onExplain}>
            <Icon name="spark" />
            基于选中段回答
          </button>
        </section>
      )}

      {activeTab === "笔记" && (
        <section className="sidebar-section">
          <h2>阅读笔记</h2>
          <label className="question-box">
            <span>绑定到 {selectedBlock.id}</span>
            <textarea value={draftNote} onChange={(event) => setDraftNote(event.target.value)} rows={4} />
          </label>
          <button className="primary-action full-width" type="button" onClick={addNote}>
            <Icon name="plus" />
            添加笔记
          </button>
          <div className="note-list">
            {notes.map((note) => (
              <article key={note.id}>
                <span>{note.blockId}</span>
                <p>{note.text}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === "概念" && (
        <section className="sidebar-section">
          <h2>候选概念</h2>
          <div className="concept-chip-list">
            {conceptList.map((concept) => (
              <button type="button" key={concept.label}>
                {concept.label}
                <span>{concept.count}</span>
              </button>
            ))}
          </div>
          <div className="answer-card">
            <strong>投影边界</strong>
            <p>当前模块只收集候选概念和证据引用；写入 `accepted_graph` 前仍应经过现有人工审核流程。</p>
          </div>
          <button className="primary-action full-width" type="button" onClick={onSave}>
            <Icon name="save" />
            保存到知识库
          </button>
        </section>
      )}
    </aside>
  );
}
