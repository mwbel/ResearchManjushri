const state = {
  mode: "web",
  domains: [],
  graphDomain: "",
  conceptCatalog: [],
  currentConcept: "",
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
      (item) => `
        <div class="domain-item">
          <div class="domain-head">
            <div class="domain-title">${escapeHtml(item.label)}</div>
            <div class="pill">${escapeHtml(item.slug)}</div>
          </div>
          <div class="meta">${escapeHtml(item.source_count)} sources · ${escapeHtml(item.wiki_page_count)} wiki pages</div>
          <div class="meta">${escapeHtml(item.domain_page || "wiki/domains/...")}</div>
        </div>
      `,
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

function renderWikiPage(page) {
  state.currentConcept = page.id;
  state.conceptCatalog = page.catalog || state.conceptCatalog;
  $("#wikiArticle").innerHTML = `
    <div class="wiki-kicker">${escapeHtml(page.domain_label || page.domain || "Concept")}</div>
    <h1>${escapeHtml(page.title)}</h1>
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

async function loadConceptPage(slug, domain = state.graphDomain) {
  if (!slug) return;
  const page = await api(`/api/concepts/page?slug=${encodeURIComponent(slug)}&domain=${encodeURIComponent(domain || "")}`);
  renderWikiPage(page);
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
      loadConceptPage(item.path ? item.path.split("/").pop().replace(/\.md$/, "") : item.id);
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
          </div>
        </div>
      `;
    })
    .join("");
}

async function refresh() {
  const [domainData, recentData] = await Promise.all([
    api("/api/domains"),
    api("/api/sources/recent?limit=8"),
  ]);
  state.domains = domainData.domains;
  renderDomainSelect(state.domains);
  renderGraphDomainSelect(state.domains);
  renderDomains(state.domains);
  renderRecent(recentData.sources);
  await loadConceptGraph(state.graphDomain);
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

async function moveSourceDomain(path) {
  const select = document.querySelector(`[data-domain-for="${CSS.escape(path)}"]`);
  if (!select) return;
  const domain = select.value;
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
    const moveButton = event.target.closest("[data-move-path]");
    if (moveButton) {
      moveSourceDomain(moveButton.dataset.movePath);
    }
  });
  $("#rebuildButton").addEventListener("click", rebuildNetworks);
  $("#graphDomainSelect").addEventListener("change", () => loadConceptGraph($("#graphDomainSelect").value));
  $("#refreshGraphButton").addEventListener("click", () => loadConceptGraph($("#graphDomainSelect").value));
  $(".concept-panel").addEventListener("click", (event) => {
    const conceptLink = event.target.closest("[data-concept-slug]");
    if (!conceptLink) return;
    loadConceptPage(conceptLink.dataset.conceptSlug);
  });
  $("#clearOutput").addEventListener("click", () => setOutput("Ready."));
}

async function init() {
  $("#date").value = today;
  bindEvents();
  switchMode("web");
  try {
    await refresh();
  } catch (error) {
    setOutput(`Error: ${error.message}`);
  }
}

init();
