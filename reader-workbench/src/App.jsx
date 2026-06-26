import { useMemo, useState } from "react";
import { demoDocument } from "./data/demoDocument.js";
import TopToolbar from "./components/TopToolbar.jsx";
import LibraryRail from "./components/LibraryRail.jsx";
import OriginalPane from "./components/OriginalPane.jsx";
import TranslationPane from "./components/TranslationPane.jsx";
import AISidebar from "./components/AISidebar.jsx";

function eventText(kind, blockId) {
  const time = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  if (kind === "save") return `${time} 保存 ${blockId} 的解释、笔记和候选概念`;
  if (kind === "explain") return `${time} 生成 ${blockId} 的上下文解释`;
  return `${time} 更新阅读状态`;
}

export default function App() {
  const [selectedBlockId, setSelectedBlockId] = useState(demoDocument.page.blocks[0].id);
  const [zoom, setZoom] = useState(100);
  const [autoTranslate, setAutoTranslate] = useState(true);
  const [syncScroll, setSyncScroll] = useState(true);
  const [query, setQuery] = useState("");
  const [notes, setNotes] = useState([
    {
      id: "n1",
      blockId: "p12-b4",
      text: "这里可以转成 wiki 概念：部署 agent 与领导 agent 的差距。",
    },
  ]);
  const [log, setLog] = useState([
    { id: "e1", text: "17:32 载入 demo 文档" },
    { id: "e2", text: "17:33 读取 page 12 blocks" },
  ]);

  const selectedBlock = useMemo(
    () => demoDocument.page.blocks.find((block) => block.id === selectedBlockId) || demoDocument.page.blocks[0],
    [selectedBlockId],
  );

  function pushEvent(kind) {
    setLog((current) => [
      { id: crypto.randomUUID(), text: eventText(kind, selectedBlock.id) },
      ...current.slice(0, 5),
    ]);
  }

  return (
    <div className="app-shell">
      <TopToolbar
        document={demoDocument}
        zoom={zoom}
        setZoom={setZoom}
        autoTranslate={autoTranslate}
        setAutoTranslate={setAutoTranslate}
        syncScroll={syncScroll}
        setSyncScroll={setSyncScroll}
        onSave={() => pushEvent("save")}
      />

      <main className="reader-layout">
        <LibraryRail activeId={demoDocument.id} log={log} />
        <OriginalPane
          blocks={demoDocument.page.blocks}
          selectedBlockId={selectedBlockId}
          setSelectedBlockId={setSelectedBlockId}
          zoom={zoom}
          query={query}
          setQuery={setQuery}
        />
        <TranslationPane
          blocks={demoDocument.page.blocks}
          selectedBlockId={selectedBlockId}
          setSelectedBlockId={setSelectedBlockId}
          autoTranslate={autoTranslate}
        />
        <AISidebar
          document={demoDocument}
          selectedBlock={selectedBlock}
          notes={notes}
          setNotes={setNotes}
          onExplain={() => pushEvent("explain")}
          onSave={() => pushEvent("save")}
        />
      </main>
    </div>
  );
}
