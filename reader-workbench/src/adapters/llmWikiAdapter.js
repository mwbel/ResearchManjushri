const API_BASE = import.meta.env.VITE_LLM_WIKI_API_BASE || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json();
}

export const llmWikiAdapter = {
  listSources(domain) {
    const query = domain ? `?domain=${encodeURIComponent(domain)}` : "";
    return request(`/api/sources${query}`);
  },

  getConceptGraph(domain) {
    return request(`/api/concepts/graph?domain=${encodeURIComponent(domain)}`);
  },

  createSource(payload) {
    return request("/api/sources", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  reviewConcept(sourceId, candidateId, action, payload = {}) {
    return request(
      `/api/sources/${encodeURIComponent(sourceId)}/concept-candidates/${encodeURIComponent(candidateId)}/${encodeURIComponent(action)}`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },
};
