import React, { useEffect, useState } from "react";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { Dialog } from "@headlessui/react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function App() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ sprint_id: "", goal: "" });

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/ledger/entries`);
      const data = await res.json();
      setEntries(data.entries || []);
    } catch {
      toast.error("⚠️ Failed to fetch ledger entries");
    }
    setLoading(false);
  };

  const addEntry = async () => {
    if (!form.sprint_id || !form.goal) {
      toast.warn("Please fill out all fields");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/ledger/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sprint_id: form.sprint_id,
          goal: form.goal,
          artifacts: ["frontend"],
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        toast.success("✅ Entry added successfully");
        setShowModal(false);
        setForm({ sprint_id: "", goal: "" });
        fetchEntries();
      } else {
        toast.error("❌ Failed to add entry");
      }
    } catch {
      toast.error("⚠️ Network error while adding entry");
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  return (
    <div className={dark ? "bg-gray-900 text-white min-h-screen" : "bg-gray-100 text-gray-900 min-h-screen"}>
      <div className="flex justify-between items-center p-4 shadow-md bg-gray-200 dark:bg-gray-800">
        <h1 className="text-xl font-bold">Ledger Dashboard Pro</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setDark(!dark)}
            className="px-3 py-1 rounded bg-gray-700 text-white hover:bg-gray-600"
          >
            {dark ? "☀️ Light" : "🌙 Dark"}
          </button>
          <button
            onClick={() => fetchEntries()}
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-500"
          >
            Refresh
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-500"
          >
            + New Entry
          </button>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <p>Loading...</p>
        ) : entries.length ? (
          entries.map((e: any) => (
            <div key={e.id} className="p-4 my-2 bg-white dark:bg-gray-700 rounded shadow">
              <p className="text-sm text-gray-500">#{e.id} • {new Date(e.timestamp * 1000).toLocaleString()}</p>
              <p><strong>Sprint:</strong> {e.sprint_id}</p>
              <p><strong>Hash:</strong> {e.manifest_hash}</p>
              <p><strong>Signature:</strong> {e.signature}</p>
            </div>
          ))
        ) : (
          <p>No ledger entries found.</p>
        )}
      </div>

      <Dialog open={showModal} onClose={() => setShowModal(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg w-80">
            <Dialog.Title className="text-lg font-bold mb-4">New Ledger Entry</Dialog.Title>
            <input
              placeholder="Sprint ID"
              value={form.sprint_id}
              onChange={(e) => setForm({ ...form, sprint_id: e.target.value })}
              className="w-full mb-3 p-2 rounded border dark:bg-gray-700"
            />
            <input
              placeholder="Goal"
              value={form.goal}
              onChange={(e) => setForm({ ...form, goal: e.target.value })}
              className="w-full mb-4 p-2 rounded border dark:bg-gray-700"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowModal(false)} className="px-3 py-1 rounded bg-gray-500 text-white hover:bg-gray-400">
                Cancel
              </button>
              <button onClick={addEntry} className="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-500">
                Save
              </button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>

      <ToastContainer position="bottom-right" theme={dark ? "dark" : "light"} />
    </div>
  );
}
