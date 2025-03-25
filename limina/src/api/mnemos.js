import axios from "axios";

const API_BASE = import.meta.env.VITE_MNEMOS_API || "http://localhost:8000";

export async function fetchGraph() {
  const res = await axios.get(`${API_BASE}/graph`);
  return res.data;
}

export async function createNode({ label, type, meta }) {
  const payload = { label, type, meta };
  console.log("📤 Sending node to", `${API_BASE}/node`, payload);

  try {
    const res = await axios.post(`${API_BASE}/node`, payload, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    console.log("✅ Node created:", res.data);
    return res.data;
  } catch (err) {
    console.error("❌ Failed to create node:", err);
    throw err;
  }
}

export async function createLink({ source, target, relation }) {
  return axios.post(`${API_BASE}/link`, {
    source,
    target,
    relation,
  });
}
