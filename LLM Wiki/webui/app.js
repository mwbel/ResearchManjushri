const state = {
  mode: "web",
  domains: [],
  selectedDomain: "",
  graphDomain: "",
  conceptCatalog: [],
  currentConcept: "",
  currentConceptPage: null,
  sciverseItems: [],
  paperResultSets: {},
  paperResultMeta: {},
  sciverseQuery: "",
  sciverseContext: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const today = new Date().toISOString().slice(0, 10);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setOutput(value) {
  $("#output").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",", 2)[1] : result);
    };
    reader.onerror = () => reject(reader.error || new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

function setBusy(isBusy) {
  $("#sourceForm").classList.toggle("is-busy", isBusy);
}

function setIntakeVisible(isVisible) {
  $("#intakePanel").classList.toggle("hidden", !isVisible);
  $("#showIntakeButton").classList.toggle("hidden", isVisible);
}

function setScienceTrackerVisible(isVisible) {
  $("#scienceTrackerPanel").classList.toggle("hidden", !isVisible);
  $("#showScienceTrackerButton").classList.toggle("hidden", isVisible);
}

function truncateText(value, limit = 28) {
  const text = String(value ?? "");
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function switchMode(mode) {
  state.mode = mode;
  $("#sourceType").value = mode;
  $$(".segment").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  $$(".web-only").forEach((node) => node.classList.toggle("hidden", mode !== "web"));
  $$(".local-only").forEach((node) => node.classList.toggle("hidden", mode !== "local"));

  const kind = $("#kind");
  if (mode === "web") kind.value = "article";
  if (mode === "local") kind.value = "paper";
  if (mode === "note") kind.value = "note";
}

function toggleNewDomainFields() {
  const isNewDomain = $("#domain").value === "__new__";
  $$(".new-domain-only").forEach((node) => node.classList.toggle("hidden", !isNewDomain));
  $("#newDomainLabel").required = isNewDomain;
}

function formPayload() {
  const mode = state.mode;
  const domain = $("#domain").value;
  return {
    title: $("#title").value.trim(),
    domain,
    new_domain_label: domain === "__new__" ? $("#newDomainLabel").value.trim() : "",
    new_domain_slug: domain === "__new__" ? $("#newDomainSlug").value.trim() : "",
    kind: $("#kind").value,
    date: $("#date").value,
    status: $("#status").value,
    source_type: mode,
    source_url: mode === "web" ? $("#sourceUrl").value.trim() : "",
    local_path: mode === "local" ? $("#localPath").value.trim() : "",
    author: $("#author").value.trim(),
    published: $("#published").value.trim(),
    tags: $("#tags").value.trim(),
    context: $("#context").value.trim(),
    original_content: $("#originalContent").value.trim(),
    notes: $("#notes").value.trim(),
    auto_ingest: $("#autoIngest").checked,
    concept_network: $("#conceptNetwork").checked,
    rebuild_domain: $("#rebuildDomain").checked,
    rebuild_index: $("#rebuildIndex").checked,
    run_lint: $("#runLint").checked,
  };
}

async function uploadSelectedLocalFile() {
  const fileInput = $("#localFile");
  const file = fileInput.files && fileInput.files[0];
  if (state.mode !== "local" || !file) {
    return null;
  }
  const payload = formPayload();
  const contentBase64 = await fileToBase64(file);
  const upload = await api("/api/uploads", {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      content_base64: contentBase64,
      date: payload.date,
      domain: payload.domain,
      new_domain_label: payload.new_domain_label,
      new_domain_slug: payload.new_domain_slug,
    }),
  });
  $("#localPath").value = upload.absolute_path;
  return upload;
}

function renderDomains(domains) {
  const root = $("#domainList");
  if (!domains.length) {
    root.innerHTML = `<div class="empty">暂无学科</div>`;
    return;
  }
  root.innerHTML = domains
    .map(
      (item) => {
        const selected = item.slug === (state.selectedDomain || state.graphDomain) ? " is-selected" : "";
        return `
        <div class="domain-item${selected}" role="button" tabindex="0" data-domain-slug="${escapeHtml(item.slug)}">
          <div class="domain-head">
            <div class="domain-title">${escapeHtml(item.label)}</div>
            <div class="pill">${escapeHtml(item.slug)}</div>
          </div>
          <div class="meta">${escapeHtml(item.source_count)} sources · ${escapeHtml(item.wiki_page_count)} wiki pages</div>
          <div class="meta">${escapeHtml(item.domain_page || "wiki/domains/...")}</div>
          <div class="domain-actions">
            <button class="danger-inline" type="button" data-domain-delete="${escapeHtml(item.slug)}" aria-label="删除学科 ${escapeHtml(item.label)}">删除学科</button>
          </div>
        </div>
      `;
      },
    )
    .join("");
}

function renderDomainSelect(domains) {
  const select = $("#domain");
  const current = select.value || "tibetan-astronomy-calendar";
  select.innerHTML = domains
    .map((item) => `<option value="${escapeHtml(item.slug)}">${escapeHtml(item.label)}</option>`)
    .join("") + `<option value="__new__">＋ 新增学科</option>`;
  if (current === "__new__") {
    select.value = "__new__";
  } else {
    select.value = domains.some((item) => item.slug === current) ? current : domains[0]?.slug || "general";
  }
  toggleNewDomainFields();
}

function renderGraphDomainSelect(domains) {
  const select = $("#graphDomainSelect");
  const current = state.graphDomain || "ai智能体";
  select.innerHTML = domains
    .map((item) => `<option value="${escapeHtml(item.slug)}">${escapeHtml(item.label)}</option>`)
    .join("");
  select.value = domains.some((item) => item.slug === current) ? current : domains[0]?.slug || "general";
  state.graphDomain = select.value;
}

function domainOptions(currentDomain) {
  return state.domains
    .map((domain) => {
      const selected = domain.slug === currentDomain ? "selected" : "";
      return `<option value="${escapeHtml(domain.slug)}" ${selected}>${escapeHtml(domain.label)}</option>`;
    })
    .join("");
}

function graphNodePositions(nodes, width, height) {
  const centerX = width / 2;
  const centerY = height / 2;
  const radiusX = Math.max(120, width * 0.36);
  const radiusY = Math.max(90, height * 0.34);
  const count = Math.max(nodes.length, 1);
  const positions = new Map();
  nodes.forEach((node, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count;
    positions.set(node.id, {
      x: centerX + Math.cos(angle) * radiusX,
      y: centerY + Math.sin(angle) * radiusY,
    });
  });
  return positions;
}

function graphVisibleData(data) {
  const edgeNodeIds = new Set();
  data.edges.forEach((edge) => {
    edgeNodeIds.add(edge.source);
    edgeNodeIds.add(edge.target);
  });
  const visibleNodes = data.nodes
    .filter((node) => edgeNodeIds.size === 0 || edgeNodeIds.has(node.id))
    .slice(0, 32);
  const visibleNodeIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = data.edges
    .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
    .slice(0, 48);
  return { visibleNodes, visibleEdges };
}

function renderRelationTable(visibleEdges) {
  $("#relationTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Source</th>
          <th>Relation</th>
          <th>Target</th>
          <th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        ${
          visibleEdges.length
            ? visibleEdges
                .map(
                  (edge) => `
                    <tr>
                      <td><button class="table-concept-link" type="button" data-concept-slug="${escapeHtml(edge.source)}">${escapeHtml(edge.source_label)}</button></td>
                      <td>${escapeHtml(edge.relation)}</td>
                      <td><button class="table-concept-link" type="button" data-concept-slug="${escapeHtml(edge.target)}">${escapeHtml(edge.target_label)}</button></td>
                      <td>${escapeHtml(edge.evidence || edge.concept_page)}</td>
                    </tr>
                  `,
                )
                .join("")
            : `<tr><td colspan="4">暂无关系</td></tr>`
        }
      </tbody>
    </table>
  `;
}

function renderGraphDetail(content) {
  const detail = $("#graphDetail");
  if (detail) detail.innerHTML = content;
}

function regexEscape(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function inlineWikiText(text, currentId = "") {
  const placeholders = [];
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, (_, code) => {
    const token = `@@P${placeholders.length}@@`;
    placeholders.push(`<code>${escapeHtml(code)}</code>`);
    return token;
  });
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label) => {
    const token = `@@P${placeholders.length}@@`;
    placeholders.push(`<span class="wiki-ref">${escapeHtml(label)}</span>`);
    return token;
  });

  const concepts = state.conceptCatalog
    .filter((item) => item.id !== currentId && item.label && item.label.length >= 2)
    .sort((a, b) => b.label.length - a.label.length)
    .slice(0, 120);
  if (concepts.length) {
    const byLabel = new Map(concepts.map((item) => [item.label, item]));
    const pattern = new RegExp(concepts.map((item) => regexEscape(item.label)).join("|"), "g");
    html = html.replace(pattern, (match) => {
      const concept = byLabel.get(match);
      if (!concept) return match;
      return `<button class="wiki-link" type="button" data-concept-slug="${escapeHtml(concept.slug)}">${escapeHtml(match)}</button>`;
    });
  }

  placeholders.forEach((value, index) => {
    html = html.replaceAll(`@@P${index}@@`, value);
  });
  return html;
}

function renderMarkdownArticle(markdown, currentId) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let inList = false;
  const closeList = () => {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      return;
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      closeList();
      const headingDepth = Math.min(heading[1].length, 3);
      html.push(`<h${headingDepth}>${inlineWikiText(heading[2], currentId)}</h${headingDepth}>`);
      return;
    }
    if (trimmed.startsWith("- ")) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${inlineWikiText(trimmed.slice(2), currentId)}</li>`);
      return;
    }
    closeList();
    html.push(`<p>${inlineWikiText(trimmed, currentId)}</p>`);
  });
  closeList();
  return html.join("");
}

function conceptBrief(page) {
  const title = String(page.title || "").trim().toLowerCase();
  if (title === "skills" || title === "skill") {
    return `
      <section class="concept-brief">
        <div class="concept-brief-title">简明解释</div>
        <p>在 AI Agent 语境里，Skill 是一个可被模型按需加载的能力包。它通常把任务说明、步骤、脚本、模板和资源放在一起，让通用 Agent 在遇到特定任务时获得更稳定的执行方式。</p>
        <ul>
          <li>它解决的是“怎么完成一类任务”，例如写作、做 PPT、处理表格或调用某套工作流。</li>
          <li>它和 MCP 不同：MCP 更像工具/数据调用协议，Skill 更像任务方法包和操作手册。</li>
          <li>放进知识库时，建议把它理解为“Agent 能力封装机制”，而不是某个具体产品名。</li>
        </ul>
      </section>
    `;
  }
  if ((page.summary || "").includes("等待人工整理定义")) {
    return `
      <section class="concept-brief">
        <div class="concept-brief-title">待整理概念</div>
        <p>这个页面目前主要来自自动抽取。下面的证据可以帮助判断它是否值得保留为独立概念，但还需要补充清晰定义、边界和例子。</p>
      </section>
    `;
  }
  return "";
}

function isNoisyRelatedConcept(item) {
  const text = `${item.slug || ""} ${item.label || ""}`.toLowerCase();
  return [
    "anthropic",
    "claude",
    "openai",
    "github",
    "cursor",
    "mulerun",
    "crea",
    "creator",
    "simon",
    "yann-lecun",
    "article-copilot",
    "ai-partner-skill",
  ].some((term) => text.includes(term));
}

function conceptNeedsDecision(page) {
  const tags = page.tags || [];
  const summary = page.summary || "";
  const body = page.body || "";
  return tags.includes("auto-concept")
    || summary.includes("自动提取")
    || summary.includes("等待人工整理")
    || body.includes("这个概念是否应该保留为独立页面");
}

function renderConceptActionState(page) {
  const keepButton = $("#keepConceptButton");
  if (!keepButton) return;
  const showKeep = page && conceptNeedsDecision(page);
  keepButton.classList.toggle("hidden", !showKeep);
  keepButton.disabled = !showKeep;
}

function renderWikiPage(page) {
  state.currentConcept = page.id;
  state.currentConceptPage = page;
  state.conceptCatalog = page.catalog || state.conceptCatalog;
  renderConceptActionState(page);
  $("#wikiArticle").innerHTML = `
    <div class="wiki-kicker">${escapeHtml(page.domain_label || page.domain || "Concept")}</div>
    <h1>${escapeHtml(page.title)}</h1>
    ${conceptBrief(page)}
    <p class="wiki-summary">${escapeHtml(page.summary || "暂无摘要。")}</p>
    <dl class="wiki-infobox">
      <div><dt>Status</dt><dd>${escapeHtml(page.status || "active")}</dd></div>
      <div><dt>Updated</dt><dd>${escapeHtml(page.updated || "unknown")}</dd></div>
      <div><dt>Path</dt><dd>${escapeHtml(page.path)}</dd></div>
    </dl>
    <div class="wiki-body">${renderMarkdownArticle(page.body, page.id)}</div>
  `;

  $("#wikiConceptList").innerHTML = (page.catalog || [])
    .filter((item) => item.slug !== page.slug)
    .filter((item) => !isNoisyRelatedConcept(item))
    .slice(0, 28)
    .map(
      (item) => `
        <button class="wiki-pill-link" type="button" data-concept-slug="${escapeHtml(item.slug)}">
          ${escapeHtml(item.label)}
        </button>
      `,
    )
    .join("") || `<div class="empty">暂无相关概念</div>`;

	  $("#wikiEdgeList").innerHTML = (page.related_edges || [])
    .slice(0, 12)
    .map(
      (edge) => `
        <button class="wiki-edge-card" type="button" data-concept-slug="${escapeHtml(edge.source === page.id ? edge.target : edge.source)}">
          <strong>${escapeHtml(edge.source_label)}</strong>
          <span>${escapeHtml(edge.relation)}</span>
          <strong>${escapeHtml(edge.target_label)}</strong>
          <p>${escapeHtml(edge.evidence || edge.concept_page || "")}</p>
        </button>
      `,
    )
	    .join("") || `<div class="empty">暂无关系证据</div>`;
}

function focusConceptDetail() {
  const panel = document.querySelector(".concept-detail-panel");
  if (!panel) return;
  if (window.innerWidth <= 1240) {
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  panel.classList.remove("is-highlighted");
  window.setTimeout(() => panel.classList.add("is-highlighted"), 0);
  window.setTimeout(() => panel.classList.remove("is-highlighted"), 1400);
}

async function loadConceptPage(slug, domain = state.graphDomain, options = {}) {
  if (!slug) return;
  const page = await api(`/api/concepts/page?slug=${encodeURIComponent(slug)}&domain=${encodeURIComponent(domain || "")}`);
  renderWikiPage(page);
  if (options.focusDetail) {
    focusConceptDetail();
  }
}

async function deleteCurrentConcept() {
  if (!state.currentConcept) {
    setOutput("请先选择一个概念。");
    return;
  }
  const title = $("#wikiArticle h1")?.textContent || state.currentConcept;
  const ok = window.confirm(`删除概念“${title}”？这会删除概念页，并清理指向它的自动关系。`);
  if (!ok) return;
  setBusy(true);
  try {
    const result = await api("/api/concepts/delete", {
      method: "POST",
      body: JSON.stringify({
        slug: state.currentConcept,
        domain: state.graphDomain,
        rebuild_domain: true,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    state.currentConcept = "";
    state.currentConceptPage = null;
    renderConceptActionState(null);
    $("#wikiArticle").innerHTML = "";
    $("#wikiConceptList").innerHTML = "";
    $("#wikiEdgeList").innerHTML = "";
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function keepCurrentConcept() {
  if (!state.currentConceptPage?.slug) {
    setOutput("请先选择一个待整理概念。");
    return;
  }
  await applyConceptDecision(state.currentConceptPage.slug, "promote");
}

function renderD3ConceptGraph(data, visibleNodes, visibleEdges) {
  const root = $("#conceptGraph");
  const width = 980;
  const height = 520;
  root.innerHTML = `
    <div class="graph-stage">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(data.domain_label)} 概念网络"></svg>
      <div id="graphDetail" class="graph-detail">点击节点或连线查看来源证据。</div>
    </div>
  `;

  const nodes = visibleNodes.map((node) => ({ ...node }));
  const nodeIds = new Set(nodes.map((node) => node.id));
  const links = visibleEdges
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .map((edge) => ({ ...edge }));
  const degree = new Map(nodes.map((node) => [node.id, 0]));
  links.forEach((link) => {
    degree.set(link.source, (degree.get(link.source) || 0) + 1);
    degree.set(link.target, (degree.get(link.target) || 0) + 1);
  });

  const d3 = window.d3;
  const svg = d3.select("#conceptGraph svg");
  const graph = svg.append("g").attr("class", "graph-viewport");
  const color = d3.scaleOrdinal()
    .domain(["hub", "concept", "relation"])
    .range(["#246b5f", "#8fb8ad", "#d3a05f"]);

  svg.call(
    d3.zoom()
      .scaleExtent([0.45, 2.8])
      .on("zoom", (event) => graph.attr("transform", event.transform)),
  );

  graph.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 18)
    .attr("refY", 0)
    .attr("markerWidth", 7)
    .attr("markerHeight", 7)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5");

  const link = graph.append("g")
    .attr("class", "graph-links")
    .selectAll("path")
    .data(links)
    .join("path")
    .attr("class", "graph-link")
    .attr("marker-end", "url(#arrow)")
    .on("click", (event, edge) => {
      event.stopPropagation();
      renderGraphDetail(`
        <strong>${escapeHtml(edge.source_label)}</strong>
        <span>${escapeHtml(edge.relation)}</span>
        <strong>${escapeHtml(edge.target_label)}</strong>
        <p>${escapeHtml(edge.evidence || edge.concept_page || "暂无证据文本")}</p>
      `);
    });

  const linkLabel = graph.append("g")
    .attr("class", "graph-link-labels")
    .selectAll("text")
    .data(links)
    .join("text")
    .attr("class", "graph-link-label")
    .text((edge) => truncateText(edge.relation, 8));

  const node = graph.append("g")
    .attr("class", "graph-nodes")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", "graph-node d3-node")
    .call(
      d3.drag()
        .on("start", (event, item) => {
          if (!event.active) simulation.alphaTarget(0.25).restart();
          item.fx = item.x;
          item.fy = item.y;
        })
        .on("drag", (event, item) => {
          item.fx = event.x;
          item.fy = event.y;
        })
        .on("end", (event, item) => {
          if (!event.active) simulation.alphaTarget(0);
          item.fx = null;
          item.fy = null;
        }),
    )
    .on("click", (event, item) => {
      event.stopPropagation();
      const related = links.filter((edge) => edge.source === item.id || edge.target === item.id);
      renderGraphDetail(`
        <strong>${escapeHtml(item.label)}</strong>
        <span>${escapeHtml(item.path || "concept")}</span>
        <p>${related.length} 条关系。${related[0] ? escapeHtml(related[0].evidence || related[0].concept_page || "") : ""}</p>
      `);
      loadConceptPage(item.path ? item.path.split("/").pop().replace(/\.md$/, "") : item.id, state.graphDomain, { focusDetail: true });
    });

  node.append("circle")
    .attr("r", (item) => Math.min(34, 18 + (degree.get(item.id) || 0) * 2.5))
    .attr("fill", (item) => color((degree.get(item.id) || 0) >= 4 ? "hub" : "concept"));

  node.append("text")
    .attr("dy", "0.35em")
    .text((item) => truncateText(item.label, 12));

  node.append("title").text((item) => `${item.label}${item.path ? ` · ${item.path}` : ""}`);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((item) => item.id).distance(118).strength(0.58))
    .force("charge", d3.forceManyBody().strength(-390))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide().radius((item) => Math.min(46, 30 + (degree.get(item.id) || 0) * 2.5)))
    .force("x", d3.forceX(width / 2).strength(0.04))
    .force("y", d3.forceY(height / 2).strength(0.04));

  simulation.on("tick", () => {
    link.attr("d", (edge) => {
      const dx = edge.target.x - edge.source.x;
      const dy = edge.target.y - edge.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy) * 1.35;
      return `M${edge.source.x},${edge.source.y}A${dr},${dr} 0 0,1 ${edge.target.x},${edge.target.y}`;
    });
    linkLabel
      .attr("x", (edge) => (edge.source.x + edge.target.x) / 2)
      .attr("y", (edge) => (edge.source.y + edge.target.y) / 2 - 6);
    node.attr("transform", (item) => `translate(${item.x},${item.y})`);
  });
}

function renderStaticConceptGraph(data, visibleNodes, visibleEdges) {
  const root = $("#conceptGraph");
  if (!visibleNodes.length) {
    root.innerHTML = `<div class="empty">暂无可视化概念关系。补跑 Ingest 并勾选“概念网络”后会生成。</div>`;
    return;
  }

  const width = 900;
  const height = 430;
  const positions = graphNodePositions(visibleNodes, width, height);
  const edgesSvg = visibleEdges
    .map((edge) => {
      const source = positions.get(edge.source);
      const target = positions.get(edge.target);
      if (!source || !target) return "";
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      return `
        <g class="graph-edge">
          <line x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" marker-end="url(#arrow)" />
          <text x="${midX}" y="${midY - 5}">${escapeHtml(truncateText(edge.relation, 10))}</text>
        </g>
      `;
    })
    .join("");

  const nodesSvg = visibleNodes
    .map((node) => {
      const point = positions.get(node.id);
      return `
        <g class="graph-node">
          <circle cx="${point.x}" cy="${point.y}" r="28" />
          <text x="${point.x}" y="${point.y + 4}">${escapeHtml(truncateText(node.label, 12))}</text>
          <title>${escapeHtml(node.label)}${node.path ? ` · ${escapeHtml(node.path)}` : ""}</title>
        </g>
      `;
    })
    .join("");

  root.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(data.domain_label)} 概念网络">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L8,4 L0,8 Z"></path>
        </marker>
      </defs>
      ${edgesSvg}
      ${nodesSvg}
    </svg>
  `;
}

function renderConceptGraph(data) {
  $("#graphSummary").textContent = `${data.domain_label} · ${data.concept_count} concepts · ${data.relation_count} relations · 可缩放/拖拽`;
  state.conceptCatalog = data.nodes.map((node) => ({
    id: node.id,
    slug: node.path ? node.path.split("/").pop().replace(/\.md$/, "") : node.id,
    label: node.label,
    path: node.path || "",
  }));
  const { visibleNodes, visibleEdges } = graphVisibleData(data);
  if (!visibleNodes.length) {
    $("#conceptGraph").innerHTML = `<div class="empty">暂无可视化概念关系。补跑 Ingest 并勾选“概念网络”后会生成。</div>`;
    $("#relationTable").innerHTML = "";
    state.currentConceptPage = null;
    renderConceptActionState(null);
    $("#wikiArticle").innerHTML = "";
    $("#wikiConceptList").innerHTML = "";
    $("#wikiEdgeList").innerHTML = "";
    return;
  }
  if (window.d3) {
    renderD3ConceptGraph(data, visibleNodes, visibleEdges);
  } else {
    renderStaticConceptGraph(data, visibleNodes, visibleEdges);
  }
  renderRelationTable(visibleEdges);
  const preferred = visibleNodes.find((node) => node.id === state.currentConcept)
    || visibleNodes.find((node) => node.id === "transformer")
    || visibleNodes[0];
  if (preferred) {
    loadConceptPage(preferred.path ? preferred.path.split("/").pop().replace(/\.md$/, "") : preferred.id);
  }
}

async function loadConceptGraph(domain = state.graphDomain || $("#graphDomainSelect").value) {
  if (!domain || domain === "__new__") return;
  state.graphDomain = domain;
  const data = await api(`/api/concepts/graph?domain=${encodeURIComponent(domain)}`);
  renderConceptGraph(data);
}

function renderRecent(sources) {
  const root = $("#recentList");
  if (!sources.length) {
    root.innerHTML = `<div class="empty">暂无资料</div>`;
    return;
  }
  root.innerHTML = sources
    .map((item) => {
      const locator = item.source_url || item.local_path || item.path;
      return `
        <div class="recent-item">
          <div class="recent-head">
            <div class="recent-title">${escapeHtml(item.title)}</div>
            <div class="pill">${escapeHtml(item.status)}</div>
          </div>
          <div class="meta">${escapeHtml(item.domain)} · ${escapeHtml(item.kind)}</div>
          <div class="meta">${escapeHtml(locator)}</div>
          <div class="recent-actions">
            <button class="inline-action" type="button" data-ingest-path="${escapeHtml(item.path)}">Ingest</button>
            <select class="mini-select" data-domain-for="${escapeHtml(item.path)}">
              ${domainOptions(item.domain)}
            </select>
            <button class="inline-action" type="button" data-move-path="${escapeHtml(item.path)}">修改学科</button>
            <button class="danger-inline" type="button" data-source-delete="${escapeHtml(item.path)}">删除资料</button>
          </div>
        </div>
      `;
    })
    .join("");
}

function sourceStatusOptions(current) {
  return ["inbox", "active", "archived"]
    .map((item) => `<option value="${item}" ${item === current ? "selected" : ""}>${item}</option>`)
    .join("");
}

function sourceKindOptions(current) {
  return ["article", "paper", "book", "note", "dataset", "video"]
    .map((item) => `<option value="${item}" ${item === current ? "selected" : ""}>${item}</option>`)
    .join("");
}

function renderDomainSources(data) {
  const root = $("#domainSourceList");
  const sources = data.sources || [];
  $("#sourceManagerTitle").textContent = `${data.domain_label || data.domain} · 全部资料`;
  $("#sourceManagerSummary").textContent = `当前学科包含 ${sources.length} 份入库资料，可在这里查看、修改学科、重新 ingest 或删除。`;
  if (!sources.length) {
    root.innerHTML = `<div class="empty">这个学科下暂无资料。可以点击“新增到此学科”后在左侧录入。</div>`;
    return;
  }
  root.innerHTML = sources
    .map(
      (item) => `
        <details class="source-record" data-source-path="${escapeHtml(item.path)}">
          <summary>
            <div>
              <div class="source-record-title">${escapeHtml(item.title)}</div>
              <div class="source-record-meta">${escapeHtml(item.status)} · ${escapeHtml(item.kind)} · ${escapeHtml(item.path)}</div>
              <div class="source-record-meta">${escapeHtml(truncateText(item.source_url || item.local_path || item.summary_paths?.[0] || "", 120))}</div>
            </div>
            <span class="pill">${escapeHtml(item.source_type || item.kind)}</span>
          </summary>
          <div class="source-editor">
            <label class="field field-wide">
              <span>标题</span>
              <input data-source-field="title" value="${escapeHtml(item.title)}" />
            </label>
            <label class="field">
              <span>类型</span>
              <select data-source-field="kind">${sourceKindOptions(item.kind)}</select>
            </label>
            <label class="field">
              <span>状态</span>
              <select data-source-field="status">${sourceStatusOptions(item.status)}</select>
            </label>
            <label class="field">
              <span>学科</span>
              <select data-source-domain-for="${escapeHtml(item.path)}">${domainOptions(item.domain)}</select>
            </label>
            <label class="field">
              <span>作者</span>
              <input data-source-field="author" value="${escapeHtml(item.author)}" />
            </label>
            <label class="field">
              <span>发表</span>
              <input data-source-field="published" value="${escapeHtml(item.published)}" />
            </label>
            <label class="field field-wide">
              <span>链接</span>
              <input data-source-field="source_url" value="${escapeHtml(item.source_url)}" />
            </label>
            <label class="field field-wide">
              <span>本地路径</span>
              <input data-source-field="local_path" value="${escapeHtml(item.local_path)}" />
            </label>
            <label class="field field-wide">
              <span>标签</span>
              <input data-source-field="tags" value="${escapeHtml(item.tags)}" />
            </label>
            <label class="field field-wide">
              <span>收录理由</span>
              <textarea data-source-field="context" rows="3">${escapeHtml(item.context)}</textarea>
            </label>
            <label class="field field-wide">
              <span>摘录</span>
              <textarea data-source-field="original_content" rows="4">${escapeHtml(item.original_content)}</textarea>
            </label>
            <label class="field field-wide">
              <span>备注</span>
              <textarea data-source-field="notes" rows="3">${escapeHtml(item.notes)}</textarea>
            </label>
            <div class="source-actions field-wide">
              <button class="inline-action" type="button" data-source-autosupplement="${escapeHtml(item.path)}">生成补充草稿</button>
              <button class="inline-action" type="button" data-source-ingest="${escapeHtml(item.path)}">Ingest</button>
              <button class="secondary" type="button" data-source-move="${escapeHtml(item.path)}">修改学科</button>
              <button class="secondary" type="button" data-source-save="${escapeHtml(item.path)}">保存修改</button>
              <button class="danger-button" type="button" data-source-delete="${escapeHtml(item.path)}">删除资料</button>
            </div>
          </div>
        </details>
      `,
    )
    .join("");
}

async function loadDomainSources(domain = state.selectedDomain || state.graphDomain) {
  if (!domain || domain === "__new__") return;
  const data = await api(`/api/sources?domain=${encodeURIComponent(domain)}`);
  renderDomainSources(data);
}

function focusSourceManager() {
  const panel = document.querySelector(".source-manager-panel");
  if (!panel) return;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  panel.classList.remove("is-highlighted");
  window.setTimeout(() => panel.classList.add("is-highlighted"), 0);
  window.setTimeout(() => panel.classList.remove("is-highlighted"), 1400);
}

async function openSourceInManager(path) {
  if (!path) return;
  let record = document.querySelector(`[data-source-path="${CSS.escape(path)}"]`);
  if (!record) {
    await loadDomainSources(state.selectedDomain || state.graphDomain);
    record = document.querySelector(`[data-source-path="${CSS.escape(path)}"]`);
  }
  if (!record) {
    setOutput(`没有在当前学科资料列表中找到：${path}`);
    return;
  }
  record.open = true;
  focusSourceManager();
  record.scrollIntoView({ behavior: "smooth", block: "center" });
}

function sourcePayloadFromRecord(record) {
  const payload = { path: record.dataset.sourcePath };
  record.querySelectorAll("[data-source-field]").forEach((field) => {
    payload[field.dataset.sourceField] = field.value.trim();
  });
  payload.auto_ingest = $("#autoIngest").checked;
  payload.concept_network = $("#conceptNetwork").checked;
  payload.rebuild_domain = $("#rebuildDomain").checked;
  payload.rebuild_index = $("#rebuildIndex").checked;
  payload.run_lint = $("#runLint").checked;
  return payload;
}

function fillSourceRecordFromProposal(record, proposal) {
  if (!record || !proposal) return;
  record.querySelectorAll("[data-source-field]").forEach((field) => {
    const key = field.dataset.sourceField;
    if (Object.prototype.hasOwnProperty.call(proposal, key)) {
      field.value = proposal[key] ?? "";
    }
  });
  record.classList.add("has-draft");
  const summary = record.querySelector(".source-record-meta");
  if (summary && !record.querySelector(".source-draft-note")) {
    summary.insertAdjacentHTML("afterend", `<div class="source-record-meta source-draft-note">已生成自动补充草稿，确认后点击“保存修改”生效。</div>`);
  }
}

async function saveDomainSource(path) {
  const record = document.querySelector(`[data-source-path="${CSS.escape(path)}"]`);
  if (!record) return;
  setBusy(true);
  try {
    const result = await api("/api/sources/update", {
      method: "POST",
      body: JSON.stringify(sourcePayloadFromRecord(record)),
    });
    setOutput(result);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function deleteDomainSource(path) {
  const ok = window.confirm("删除这份入库资料？将删除 raw source、对应 source summary，并移除只由它生成的自动概念；不会删除本地上传的原始文件。");
  if (!ok) return;
  setBusy(true);
  try {
    const result = await api("/api/sources/delete", {
      method: "POST",
      body: JSON.stringify({
        path,
        delete_summary: true,
        delete_orphan_concepts: true,
        rebuild_domain: true,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function deleteDomain(domain) {
  const item = state.domains.find((entry) => entry.slug === domain);
  const label = item?.label || domain;
  const ok = window.confirm(
    `删除学科“${label}”？\n\n将删除该学科的 raw source、wiki 学科页、source summary，并清理只属于它的自动概念；不会删除本地上传的原始文件。`,
  );
  if (!ok) return;
  setBusy(true);
  try {
    const result = await api("/api/domains/delete", {
      method: "POST",
      body: JSON.stringify({
        domain,
        rebuild_domains: true,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    const nextDomain = state.domains.find((entry) => entry.slug !== domain)?.slug || "general";
    state.selectedDomain = nextDomain;
    state.graphDomain = nextDomain;
    state.currentConcept = "";
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function selectDomain(domain, options = {}) {
  if (!domain || domain === "__new__") return;
  state.selectedDomain = domain;
  state.graphDomain = domain;
  if ($("#domain")) {
    $("#domain").value = domain;
    toggleNewDomainFields();
  }
  if ($("#graphDomainSelect")) {
    $("#graphDomainSelect").value = domain;
  }
  renderDomains(state.domains);
  await Promise.all([loadWorkbench(domain), loadConceptGraph(domain), loadDomainSources(domain)]);
  if (options.focusSources) {
    focusSourceManager();
  }
}

function renderStatTile(value, label) {
  return `
    <div class="stat-tile">
      <span class="stat-value">${escapeHtml(value)}</span>
      <span class="stat-label">${escapeHtml(label)}</span>
    </div>
  `;
}

function renderConceptQueue(items) {
  const root = $("#conceptQueue");
  if (!items.length) {
    root.innerHTML = `<div class="empty">当前学科暂无待整理概念</div>`;
    return;
  }
  root.innerHTML = items
    .map(
      (item) => `
        <button class="task-item is-clickable" type="button" data-concept-slug="${escapeHtml(item.slug)}">
          <div class="task-title">${escapeHtml(item.title)}</div>
          <div class="task-reason">${escapeHtml(item.reason)}</div>
          <div class="task-meta">${escapeHtml(truncateText(item.summary || item.path, 120))}</div>
        </button>
      `,
    )
    .join("");
}

function renderSourceQueue(items) {
  const root = $("#sourceQueue");
  if (!items.length) {
    root.innerHTML = `<div class="empty">当前学科暂无待补资料</div>`;
    return;
  }
  root.innerHTML = items
    .map(
      (item) => {
        const rawPath = item.raw_path || "";
        return `
        <div class="task-item">
          <div class="task-title">${escapeHtml(item.title)}</div>
          <div class="task-reason">${escapeHtml(item.reason)}</div>
          <div class="task-meta">${escapeHtml(truncateText(item.summary || item.path, 120))}</div>
          ${rawPath ? `
            <div class="task-actions">
              <button class="inline-action" type="button" data-source-open="${escapeHtml(rawPath)}">打开补充</button>
              <button class="inline-action" type="button" data-source-autosupplement="${escapeHtml(rawPath)}">生成补充草稿</button>
              <button class="inline-action" type="button" data-source-ingest="${escapeHtml(rawPath)}">重新 Ingest</button>
              <button class="danger-inline" type="button" data-source-delete="${escapeHtml(rawPath)}">删除资料</button>
            </div>
          ` : ""}
        </div>
      `;
      },
    )
    .join("");
}

function renderWorkbenchRecent(items) {
  const root = $("#workbenchRecent");
  if (!items.length) {
    root.innerHTML = `<div class="empty">当前学科暂无最近资料</div>`;
    return;
  }
  root.innerHTML = items
    .map(
      (item) => `
        <div class="task-item">
          <div class="task-title">${escapeHtml(item.title)}</div>
          <div class="task-meta">${escapeHtml(item.status)} · ${escapeHtml(item.kind)}</div>
          <div class="task-meta">${escapeHtml(truncateText(item.source_url || item.local_path || item.path, 120))}</div>
          <div class="task-actions"><button class="danger-inline" type="button" data-source-delete="${escapeHtml(item.path)}">删除资料</button></div>
        </div>
      `,
    )
    .join("");
}

function actionLabel(action) {
  return {
    delete_noise: "删除噪声",
    merge_suggested: "建议合并",
    promote: "保留转正",
    manual_review: "人工判断",
  }[action] || action;
}

function organizeItemActions(item) {
  const slug = escapeHtml(item.slug);
  const buttons = [
    `<button class="inline-action" type="button" data-concept-slug="${slug}">打开</button>`,
  ];
  if (item.action === "delete_noise") {
    buttons.push(`<button class="danger-inline" type="button" data-concept-decision="delete" data-decision-slug="${slug}">确认删除</button>`);
  } else if (item.action === "promote") {
    buttons.push(`<button class="inline-action" type="button" data-concept-decision="promote" data-decision-slug="${slug}">确认保留</button>`);
  } else {
    buttons.push(`<button class="inline-action" type="button" data-concept-decision="promote" data-decision-slug="${slug}">保留为概念</button>`);
    buttons.push(`<button class="danger-inline" type="button" data-concept-decision="delete" data-decision-slug="${slug}">删除概念</button>`);
  }
  if (item.target_slug) {
    buttons.push(`<button class="inline-action" type="button" data-concept-slug="${escapeHtml(item.target_slug)}">打开目标</button>`);
  }
  return `<div class="organize-actions">${buttons.join("")}</div>`;
}

function renderOrganizeResult(data) {
  const root = $("#organizeConceptsResult");
  const actions = data.actions || [];
  const applied = data.applied || [];
  const grouped = actions.reduce((acc, item) => {
    acc[item.action] = acc[item.action] || [];
    acc[item.action].push(item);
    return acc;
  }, {});
  const order = ["delete_noise", "promote", "merge_suggested", "manual_review"];
  root.classList.remove("hidden");
  root.innerHTML = `
    <div class="organize-head">
      <div>
        <strong>${escapeHtml(data.apply ? "已应用自动整理" : "自动整理预览")}</strong>
        <span>${escapeHtml(data.domain_label || data.domain)} · ${actions.length} concepts</span>
      </div>
      ${applied.length ? `<span class="pill">已处理 ${escapeHtml(applied.length)}</span>` : ""}
    </div>
    <div class="organize-principles">
      ${(data.principles || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
    </div>
    ${data.llm_prompt ? `
      <details class="organize-prompt">
        <summary>概念整理提示词</summary>
        <pre>${escapeHtml(data.llm_prompt)}</pre>
      </details>
    ` : ""}
    <div class="organize-grid">
      ${order
        .filter((key) => grouped[key]?.length)
        .map((key) => `
          <div class="organize-column">
            <h3>${escapeHtml(actionLabel(key))} · ${escapeHtml(grouped[key].length)}</h3>
            ${grouped[key].slice(0, 8).map((item) => `
              <div class="organize-item">
                <span>${escapeHtml(item.title)}</span>
                <small>${escapeHtml(item.reason)}</small>
                ${item.target_title ? `<small>目标：${escapeHtml(item.target_title)}</small>` : ""}
                ${organizeItemActions(item)}
              </div>
            `).join("")}
          </div>
        `)
        .join("")}
    </div>
  `;
}

async function organizeConcepts(apply = false) {
  const domain = state.selectedDomain || state.graphDomain || $("#graphDomainSelect").value;
  if (apply) {
    const ok = window.confirm("应用高置信自动整理？会删除明显噪声概念，并把证据较充分的候选概念移出待整理队列；合并建议不会自动执行。");
    if (!ok) return;
  }
  setBusy(true);
  try {
    const result = await api("/api/concepts/organize", {
      method: "POST",
      body: JSON.stringify({
        domain,
        apply,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    renderOrganizeResult(result);
    if (apply) {
      await Promise.all([loadWorkbench(domain), loadConceptGraph(domain)]);
    }
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function applyConceptDecision(slug, decision) {
  const label = decision === "delete" ? "删除这个概念？" : "保留为正式概念？";
  const ok = window.confirm(label);
  if (!ok) return;
  const domain = state.selectedDomain || state.graphDomain || $("#graphDomainSelect").value;
  setBusy(true);
  try {
    const result = await api("/api/concepts/decision", {
      method: "POST",
      body: JSON.stringify({
        slug,
        decision,
        domain,
        rebuild_domain: true,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    if (decision === "delete" && state.currentConcept === slug) {
      state.currentConcept = "";
      state.currentConceptPage = null;
      renderConceptActionState(null);
      $("#wikiArticle").innerHTML = "";
      $("#wikiConceptList").innerHTML = "";
      $("#wikiEdgeList").innerHTML = "";
    }
    await Promise.all([loadWorkbench(domain), loadConceptGraph(domain)]);
    if (decision !== "delete" && state.currentConceptPage?.slug === slug) {
      await loadConceptPage(slug, domain);
    }
    await organizeConcepts(false);
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

function firstValue(...values) {
  for (const value of values) {
    if (Array.isArray(value) && value.length) {
      const joined = value
        .map((item) => {
          if (item && typeof item === "object") return item.name || item.title || item.display_name || "";
          return item;
        })
        .filter((item) => item !== undefined && item !== null && String(item).trim())
        .join(", ");
      if (joined) return joined;
    }
    if (value !== undefined && value !== null && String(value).trim()) return value;
  }
  return "";
}

function findSciverseItems(value, depth = 0) {
  if (!value || depth > 4) return [];
  if (Array.isArray(value)) {
    const objectItems = value.filter((item) => item && typeof item === "object" && !Array.isArray(item));
    if (
      objectItems.length
      && objectItems.some((item) => item.title || item.doc_id || item.text || item.excerpt || item.abstract)
    ) {
      return objectItems;
    }
    for (const item of value) {
      const found = findSciverseItems(item, depth + 1);
      if (found.length) return found;
    }
    return [];
  }
  if (typeof value === "object") {
    const preferredKeys = ["results", "items", "papers", "chunks", "matches", "data"];
    for (const key of preferredKeys) {
      const found = findSciverseItems(value[key], depth + 1);
      if (found.length) return found;
    }
    for (const child of Object.values(value)) {
      const found = findSciverseItems(child, depth + 1);
      if (found.length) return found;
    }
  }
  return [];
}

function normalizeSciverseItem(item) {
  const metadata = item.metadata || item.paper || item.document || {};
  const venue = firstValue(
    item.venue,
    item.journal,
    item.source,
    item.publication_venue_name,
    item.publication_venue_name_unified,
    metadata.venue,
    metadata.journal,
  );
  const isScienceMain = /^science$/i.test(String(venue).trim());
  return {
    title: firstValue(item.title, item.paper_title, item.document_title, metadata.title, "Untitled paper"),
    docId: firstValue(item.doc_id, item.document_id, item.paper_id, metadata.doc_id, metadata.id),
    year: firstValue(item.year, item.publication_year, item.publication_published_year, metadata.year),
    venue,
    isScienceMain,
    authors: firstValue(item.authors, item.author, metadata.authors),
    doi: firstValue(item.doi, metadata.doi),
    score: firstValue(item.score, item.similarity, item.rank_score),
    excerpt: firstValue(item.text, item.chunk_text, item.excerpt, item.snippet, item.abstract, metadata.abstract),
  };
}

function renderPaperResults(result, rootSelector, setName, emptyMessage = "没有找到可展示的论文条目，原始 JSON 已写入结果面板。") {
  const root = $(rootSelector);
  const rawItems = findSciverseItems(result.result || result).slice(0, 8);
  const items = rawItems.map((item, index) => ({ ...normalizeSciverseItem(item), raw: item, index }));
  state.paperResultSets[setName] = items;
  state.paperResultMeta[setName] = {
    query: state.sciverseQuery,
    context: state.sciverseContext,
  };
  state.sciverseItems = items;
  if (!items.length) {
    root.innerHTML = `<div class="empty">${escapeHtml(emptyMessage)}</div>`;
    return;
  }
  root.innerHTML = items
    .map(
      (item) => `
        <div class="paper-card">
          <div class="paper-title">${escapeHtml(item.title)}</div>
          ${setName === "science" ? `<div class="paper-meta"><span class="tracker-badge ${item.isScienceMain ? "is-match" : "is-candidate"}">${item.isScienceMain ? "Science match" : "候选，需核对期刊"}</span></div>` : ""}
          <div class="paper-meta">
            ${escapeHtml([item.year, item.venue, item.authors].filter(Boolean).join(" · ") || "metadata pending")}
          </div>
          <div class="paper-meta">
            ${escapeHtml([item.docId ? `doc_id: ${item.docId}` : "", item.doi ? `DOI: ${item.doi}` : "", item.score ? `score: ${item.score}` : ""].filter(Boolean).join(" · "))}
          </div>
          ${item.excerpt ? `<div class="paper-excerpt">${escapeHtml(truncateText(item.excerpt, 260))}</div>` : ""}
          <div class="paper-actions">
            <button class="inline-action" type="button" data-paper-set="${escapeHtml(setName)}" data-sciverse-import="${item.index}">导入 source</button>
            <button class="inline-action" type="button" data-paper-set="${escapeHtml(setName)}" data-sciverse-evidence="${item.index}">补强当前概念</button>
            <button class="inline-action" type="button" data-paper-set="${escapeHtml(setName)}" data-sciverse-import-evidence="${item.index}">导入并补强</button>
          </div>
        </div>
      `,
    )
    .join("");
}

function renderSciverseResults(result) {
  renderPaperResults(result, "#sciverseResults", "sciverse");
}

function toggleSciverseFields() {
  const isMetadata = $("#sciverseSearchType").value === "metadata";
  $$(".metadata-only").forEach((node) => node.classList.toggle("hidden", !isMetadata));
  $("#sciverseMode").disabled = isMetadata;
}

function sciversePayload() {
  const searchType = $("#sciverseSearchType").value;
  const limit = Number($("#sciverseLimit").value || 5);
  const payload = {
    search_type: searchType,
    query: $("#sciverseQuery").value.trim(),
    token: $("#sciverseToken").value.trim(),
  };
  if (searchType === "metadata") {
    payload.page_size = limit;
    payload.year_from = $("#sciverseYearFrom").value.trim();
    payload.year_to = $("#sciverseYearTo").value.trim();
  } else {
    payload.top_k = limit;
    payload.mode = $("#sciverseMode").value;
  }
  return payload;
}

async function searchSciverse(event) {
  event.preventDefault();
  $("#sciverseResults").innerHTML = `<div class="empty">正在检索 Sciverse...</div>`;
  try {
    state.sciverseQuery = $("#sciverseQuery").value.trim();
    state.sciverseContext = "Sciverse 学术检索导入，用于补强当前知识网络的论文证据。";
    const result = await api("/api/sciverse/search", {
      method: "POST",
      body: JSON.stringify(sciversePayload()),
    });
    setOutput(result);
    renderSciverseResults(result);
  } catch (error) {
    $("#sciverseResults").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    setOutput(`Error: ${error.message}`);
  }
}

function scienceTrackerPayload() {
  return {
    query: $("#scienceTrackerQuery").value.trim() || "hierarchical memory",
    token: $("#sciverseToken").value.trim(),
    year_from: $("#scienceTrackerYearFrom").value.trim(),
    year_to: $("#scienceTrackerYearTo").value.trim(),
    page_size: Number($("#scienceTrackerLimit").value || 8),
  };
}

async function trackScience(event) {
  event.preventDefault();
  $("#scienceTrackerResults").innerHTML = `<div class="empty">正在追踪 Science 主刊...</div>`;
  try {
    const payload = scienceTrackerPayload();
    state.sciverseQuery = payload.query;
    state.sciverseContext = `Science 主刊追踪导入：${payload.query}`;
    const result = await api("/api/trackers/science", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setOutput(result);
    renderPaperResults(result, "#scienceTrackerResults", "science", "Science 主刊里暂未找到匹配论文；可以放宽主题词或年份。");
  } catch (error) {
    $("#scienceTrackerResults").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    setOutput(`Error: ${error.message}`);
  }
}

function sciverseItem(index, setName = "sciverse") {
  return (state.paperResultSets[setName] || state.sciverseItems)[Number(index)];
}

async function importSciverseSource(index, setName = "sciverse") {
  const item = sciverseItem(index, setName);
  if (!item) return null;
  const meta = state.paperResultMeta[setName] || {};
  const isScienceTracker = setName === "science";
  const result = await api("/api/sciverse/import-source", {
    method: "POST",
    body: JSON.stringify({
      paper: item.raw,
      domain: state.graphDomain || $("#graphDomainSelect").value || $("#domain").value,
      query: meta.query || state.sciverseQuery,
      tags: isScienceTracker ? "science-main, journal-tracker, memory" : "",
      context: meta.context || state.sciverseContext || "",
      auto_ingest: $("#autoIngest").checked,
      concept_network: false,
      rebuild_domain: $("#rebuildDomain").checked,
      rebuild_index: $("#rebuildIndex").checked,
      run_lint: $("#runLint").checked,
    }),
  });
  setOutput(result);
  await refresh();
  return result;
}

async function addSciverseEvidence(index, sourcePath = "", setName = "sciverse") {
  const item = sciverseItem(index, setName);
  if (!item) return null;
  if (!state.currentConcept) {
    throw new Error("当前没有选中的概念页，请先点击一个概念。");
  }
  const result = await api("/api/concepts/academic-evidence", {
    method: "POST",
    body: JSON.stringify({
      slug: state.currentConcept,
      paper: item.raw,
      source_path: sourcePath,
    }),
  });
  setOutput(result);
  await loadConceptPage(state.currentConcept);
  await loadWorkbench(state.graphDomain);
  return result;
}

async function importAndAddSciverseEvidence(index, setName = "sciverse") {
  const imported = await importSciverseSource(index, setName);
  const sourcePath = imported?.source?.summary || imported?.source?.path || "";
  const evidence = await addSciverseEvidence(index, sourcePath, setName);
  setOutput({ import: imported, evidence });
}

async function handlePaperResultClick(event) {
  const importButton = event.target.closest("[data-sciverse-import]");
  const evidenceButton = event.target.closest("[data-sciverse-evidence]");
  const importEvidenceButton = event.target.closest("[data-sciverse-import-evidence]");
  const button = importButton || evidenceButton || importEvidenceButton;
  if (!button) return;
  const setName = button.dataset.paperSet || "sciverse";
  setBusy(true);
  try {
    if (importEvidenceButton) {
      await importAndAddSciverseEvidence(importEvidenceButton.dataset.sciverseImportEvidence, setName);
    } else if (importButton) {
      await importSciverseSource(importButton.dataset.sciverseImport, setName);
    } else if (evidenceButton) {
      await addSciverseEvidence(evidenceButton.dataset.sciverseEvidence, "", setName);
    }
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

function renderWorkbench(data) {
  const stats = data.stats || {};
  $("#workbenchSummary").textContent = `${data.domain_label || data.domain} · ${stats.concept_queue || 0} 个概念待整理 · ${stats.source_queue || 0} 份资料待补`;
  $("#workbenchStats").innerHTML = [
    renderStatTile(stats.raw_sources || 0, "Raw Sources"),
    renderStatTile(stats.source_summaries || 0, "Source Pages"),
    renderStatTile(stats.concepts || 0, "Concepts"),
    renderStatTile(stats.relations || 0, "Relations"),
    renderStatTile(stats.concept_queue || 0, "Concept Queue"),
    renderStatTile(stats.source_queue || 0, "Source Queue"),
  ].join("");
  renderConceptQueue(data.concept_queue || []);
  renderSourceQueue(data.source_queue || []);
  renderWorkbenchRecent(data.recent_sources || []);
}

async function loadWorkbench(domain = state.graphDomain || $("#graphDomainSelect").value) {
  if (!domain || domain === "__new__") return;
  const data = await api(`/api/workbench?domain=${encodeURIComponent(domain)}`);
  renderWorkbench(data);
}

async function refresh() {
  const [domainData, recentData] = await Promise.all([
    api("/api/domains"),
    api("/api/sources/recent?limit=8"),
  ]);
  state.domains = domainData.domains;
  const availableDomains = new Set(state.domains.map((item) => item.slug));
  if (!availableDomains.has(state.selectedDomain)) {
    state.selectedDomain = state.domains[0]?.slug || "";
  }
  if (!availableDomains.has(state.graphDomain)) {
    state.graphDomain = state.selectedDomain || state.domains[0]?.slug || "";
  }
  renderDomainSelect(state.domains);
  renderGraphDomainSelect(state.domains);
  state.selectedDomain = state.selectedDomain || state.graphDomain;
  renderDomains(state.domains);
  renderRecent(recentData.sources);
  await Promise.all([
    loadWorkbench(state.selectedDomain),
    loadConceptGraph(state.selectedDomain),
    loadDomainSources(state.selectedDomain),
  ]);
}

async function submitSource(event) {
  event.preventDefault();
  setBusy(true);
  try {
    const upload = await uploadSelectedLocalFile();
    const payload = formPayload();
    const result = await api("/api/sources", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setOutput(upload ? { upload, source: result } : result);
    $("#sourceForm").reset();
    $("#date").value = today;
    $("#domain").value = result.domain;
    $("#newDomainLabel").value = "";
    $("#newDomainSlug").value = "";
    switchMode(state.mode);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function previewSource() {
  setBusy(true);
  try {
    const result = await api("/api/sources/preview", {
      method: "POST",
      body: JSON.stringify(formPayload()),
    });
    setOutput(result.content);
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function rebuildNetworks() {
  setBusy(true);
  try {
    const result = await api("/api/rebuild", {
      method: "POST",
      body: JSON.stringify({ domain: $("#domain").value, run_lint: true }),
    });
    setOutput(result);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function ingestExisting(path) {
  setBusy(true);
  try {
    const result = await api("/api/ingest", {
      method: "POST",
      body: JSON.stringify({
        path,
        overwrite_ingest: true,
        concept_network: $("#conceptNetwork").checked,
        rebuild_domain: $("#rebuildDomain").checked,
        rebuild_index: $("#rebuildIndex").checked,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

function autoSupplementPayload(path) {
  return {
    path,
    apply: false,
    auto_ingest: true,
    concept_network: $("#conceptNetwork").checked,
    rebuild_domain: $("#rebuildDomain").checked,
    rebuild_index: $("#rebuildIndex").checked,
    run_lint: $("#runLint").checked,
  };
}

async function autoSupplementSource(path, options = {}) {
  setBusy(true);
  try {
    await openSourceInManager(path);
    const result = await api("/api/sources/auto-supplement", {
      method: "POST",
      body: JSON.stringify(autoSupplementPayload(path)),
    });
    const record = document.querySelector(`[data-source-path="${CSS.escape(path)}"]`);
    fillSourceRecordFromProposal(record, result.proposal);
    setOutput(result);
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function autoSupplementQueuedSources() {
  const paths = Array.from(new Set(
    Array.from(document.querySelectorAll("#sourceQueue [data-source-autosupplement]"))
      .map((button) => button.dataset.sourceAutosupplement)
      .filter(Boolean),
  ));
  if (!paths.length) {
    setOutput("当前没有待补资料。");
    return;
  }
  const ok = window.confirm(`为当前学科的 ${paths.length} 份待补资料生成自动补充草稿？草稿会填入表单，确认后需要点击“保存修改”才会生效。`);
  if (!ok) return;
  setBusy(true);
  const results = [];
  try {
    await loadDomainSources(state.selectedDomain || state.graphDomain);
    for (const path of paths) {
      try {
        const result = await api("/api/sources/auto-supplement", {
          method: "POST",
          body: JSON.stringify(autoSupplementPayload(path)),
        });
        const record = document.querySelector(`[data-source-path="${CSS.escape(path)}"]`);
        if (record) {
          record.open = true;
          fillSourceRecordFromProposal(record, result.proposal);
        }
        results.push({ path, ok: true, result });
        setOutput({ running: path, completed: results.length, total: paths.length, latest: result });
      } catch (error) {
        results.push({ path, ok: false, error: error.message });
        setOutput({ running: path, completed: results.length, total: paths.length, error: error.message });
      }
    }
    focusSourceManager();
    setOutput({ ok: results.every((item) => item.ok), total: paths.length, results });
  } finally {
    setBusy(false);
  }
}

async function moveSourceDomain(path, select = null) {
  const domainSelect = select
    || document.querySelector(`[data-source-domain-for="${CSS.escape(path)}"]`)
    || document.querySelector(`[data-domain-for="${CSS.escape(path)}"]`);
  if (!domainSelect) return;
  const domain = domainSelect.value;
  setBusy(true);
  try {
    const result = await api("/api/sources/domain", {
      method: "POST",
      body: JSON.stringify({
        path,
        domain,
        overwrite_ingest: true,
        concept_network: $("#conceptNetwork").checked,
        rebuild_domain: true,
        rebuild_index: true,
        run_lint: $("#runLint").checked,
      }),
    });
    setOutput(result);
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

function bindEvents() {
  $$(".segment").forEach((button) => {
    button.addEventListener("click", () => switchMode(button.dataset.mode));
  });
  $("#hideIntakeButton").addEventListener("click", () => setIntakeVisible(false));
  $("#showIntakeButton").addEventListener("click", () => {
    setIntakeVisible(true);
    $("#title").focus();
  });
  $("#hideScienceTrackerButton").addEventListener("click", () => setScienceTrackerVisible(false));
  $("#showScienceTrackerButton").addEventListener("click", () => {
    setScienceTrackerVisible(true);
    $("#scienceTrackerQuery").focus();
  });
  $("#sourceForm").addEventListener("submit", submitSource);
  $("#localFile").addEventListener("change", () => {
    const file = $("#localFile").files && $("#localFile").files[0];
    if (!file) return;
    if (!$("#title").value.trim()) {
      $("#title").value = file.name.replace(/\.[^.]+$/, "");
    }
    const extension = file.name.split(".").pop().toLowerCase();
    if (["txt", "md", "markdown", "csv", "tsv"].includes(extension)) {
      $("#kind").value = "note";
    } else if (["pdf", "doc", "docx"].includes(extension)) {
      $("#kind").value = "paper";
    }
  });
  $("#domain").addEventListener("change", toggleNewDomainFields);
  $("#scienceTrackerForm").addEventListener("submit", trackScience);
  $("#scienceTrackerResults").addEventListener("click", handlePaperResultClick);
  $("#sciverseSearchType").addEventListener("change", toggleSciverseFields);
  $("#sciverseForm").addEventListener("submit", searchSciverse);
  $("#sciverseResults").addEventListener("click", handlePaperResultClick);
  $("#previewButton").addEventListener("click", previewSource);
  $("#refreshButton").addEventListener("click", async () => {
    await refresh();
    setOutput("Refreshed.");
  });
  $("#recentList").addEventListener("click", (event) => {
    const ingestButton = event.target.closest("[data-ingest-path]");
    if (ingestButton) {
      ingestExisting(ingestButton.dataset.ingestPath);
      return;
    }
    const deleteButton = event.target.closest("[data-source-delete]");
    if (deleteButton) {
      deleteDomainSource(deleteButton.dataset.sourceDelete);
      return;
    }
    const moveButton = event.target.closest("[data-move-path]");
    if (moveButton) {
      const select = moveButton.closest(".recent-item")?.querySelector("[data-domain-for]");
      moveSourceDomain(moveButton.dataset.movePath, select);
    }
  });
  $("#domainList").addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-domain-delete]");
    if (deleteButton) {
      event.stopPropagation();
      deleteDomain(deleteButton.dataset.domainDelete);
      return;
    }
    const item = event.target.closest("[data-domain-slug]");
    if (item) selectDomain(item.dataset.domainSlug, { focusSources: true });
  });
  $("#domainList").addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const item = event.target.closest("[data-domain-slug]");
    if (item) {
      event.preventDefault();
      selectDomain(item.dataset.domainSlug, { focusSources: true });
    }
  });
  $("#domainSourceList").addEventListener("click", (event) => {
    const autoSupplementButton = event.target.closest("[data-source-autosupplement]");
    const ingestButton = event.target.closest("[data-source-ingest]");
    const moveButton = event.target.closest("[data-source-move]");
    const saveButton = event.target.closest("[data-source-save]");
    const deleteButton = event.target.closest("[data-source-delete]");
    if (autoSupplementButton) {
      event.stopPropagation();
      autoSupplementSource(autoSupplementButton.dataset.sourceAutosupplement);
      return;
    }
    if (ingestButton) {
      event.stopPropagation();
      ingestExisting(ingestButton.dataset.sourceIngest);
      return;
    }
    if (moveButton) {
      event.stopPropagation();
      const select = moveButton.closest(".source-record")?.querySelector("[data-source-domain-for]");
      moveSourceDomain(moveButton.dataset.sourceMove, select);
      return;
    }
    if (saveButton) {
      event.stopPropagation();
      saveDomainSource(saveButton.dataset.sourceSave);
      return;
    }
    if (deleteButton) {
      event.stopPropagation();
      deleteDomainSource(deleteButton.dataset.sourceDelete);
    }
  });
  $("#newSourceForDomainButton").addEventListener("click", () => {
    setIntakeVisible(true);
    if (state.selectedDomain) {
      $("#domain").value = state.selectedDomain;
      toggleNewDomainFields();
    }
    $("#title").focus();
  });
  $("#refreshSourcesButton").addEventListener("click", () => loadDomainSources(state.selectedDomain));
  $("#rebuildButton").addEventListener("click", rebuildNetworks);
  $("#graphDomainSelect").addEventListener("change", async () => {
    const domain = $("#graphDomainSelect").value;
    await selectDomain(domain);
  });
  $("#refreshGraphButton").addEventListener("click", () => loadConceptGraph($("#graphDomainSelect").value));
  $("#keepConceptButton").addEventListener("click", keepCurrentConcept);
  $("#deleteConceptButton").addEventListener("click", deleteCurrentConcept);
  $("#refreshWorkbenchButton").addEventListener("click", () => loadWorkbench($("#graphDomainSelect").value));
  $("#organizeConceptsButton").addEventListener("click", () => organizeConcepts(false));
  $("#applyOrganizeConceptsButton").addEventListener("click", () => organizeConcepts(true));
  $("#autoSupplementQueueButton").addEventListener("click", autoSupplementQueuedSources);
  $(".center-stage").addEventListener("click", (event) => {
    const openSourceButton = event.target.closest("[data-source-open]");
    if (openSourceButton) {
      openSourceInManager(openSourceButton.dataset.sourceOpen);
      return;
    }
    const autoSupplementButton = event.target.closest("[data-source-autosupplement]");
    if (autoSupplementButton) {
      autoSupplementSource(autoSupplementButton.dataset.sourceAutosupplement);
      return;
    }
    const ingestSourceButton = event.target.closest("[data-source-ingest]");
    if (ingestSourceButton) {
      ingestExisting(ingestSourceButton.dataset.sourceIngest);
      return;
    }
    const deleteButton = event.target.closest("[data-source-delete]");
    if (deleteButton) {
      deleteDomainSource(deleteButton.dataset.sourceDelete);
      return;
    }
    const decisionButton = event.target.closest("[data-concept-decision]");
    if (decisionButton) {
      applyConceptDecision(decisionButton.dataset.decisionSlug, decisionButton.dataset.conceptDecision);
      return;
    }
    const conceptLink = event.target.closest("[data-concept-slug]");
    if (!conceptLink) return;
    loadConceptPage(conceptLink.dataset.conceptSlug, state.graphDomain, { focusDetail: true });
  });
  $(".composer-rail").addEventListener("click", (event) => {
    const conceptLink = event.target.closest("[data-concept-slug]");
    if (!conceptLink) return;
    loadConceptPage(conceptLink.dataset.conceptSlug, state.graphDomain, { focusDetail: true });
  });
  $("#clearOutput").addEventListener("click", () => setOutput("Ready."));
}

async function init() {
  $("#date").value = today;
  bindEvents();
  switchMode("web");
  toggleSciverseFields();
  try {
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  }
}

init();
