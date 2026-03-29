"use client";

import { useState } from "react";
import { Check, Pencil, X, AlertCircle, CheckCircle2 } from "lucide-react";
import type { SupplierRecord } from "@/types/ads";
import { saveSupplier } from "@/lib/api";
import clsx from "clsx";

interface Props {
  supplier: SupplierRecord;
  onSaved: (updated: SupplierRecord) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  Hotel:       "bg-blue-50 text-blue-700 border-blue-100",
  Restaurant:  "bg-green-50 text-green-700 border-green-100",
  Transport:   "bg-purple-50 text-purple-700 border-purple-100",
  Attraction:  "bg-orange-50 text-orange-700 border-orange-100",
  Guide:       "bg-pink-50 text-pink-700 border-pink-100",
  Other:       "bg-gray-50 text-gray-600 border-gray-100",
};

export default function SupplierRow({ supplier, onSaved }: Props) {
  const [editing, setEditing] = useState(supplier.status === "missing");
  const [form, setForm] = useState({
    address:      supplier.address ?? "",
    phone:        supplier.phone ?? "",
    email:        supplier.email ?? "",
    contact_name: supplier.contact_name ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await saveSupplier({ ...supplier, ...form, status: "confirmed" });
      setSaved(true);
      setEditing(false);
      onSaved({ ...supplier, ...form, status: "confirmed" });
    } finally {
      setSaving(false);
    }
  }

  const isMissing = supplier.status === "missing" && !saved;

  return (
    <div
      className={clsx(
        "rounded-xl border px-4 py-3 transition-colors",
        isMissing
          ? "border-amber-300 bg-amber-50"
          : "border-gray-100 bg-white hover:border-gray-200"
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm text-gray-900">{supplier.name_en}</span>
          {supplier.name_zh && (
            <span className="text-xs text-gray-400">{supplier.name_zh}</span>
          )}
          <span
            className={clsx(
              "text-xs border rounded-full px-2 py-0.5",
              CATEGORY_COLORS[supplier.category]
            )}
          >
            {supplier.category}
          </span>
          <span className="text-xs text-gray-400">
            Day{supplier.day_references.length > 1 ? "s" : ""}{" "}
            {supplier.day_references.join(", ")}
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {isMissing && (
            <span className="flex items-center gap-1 text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
              <AlertCircle size={12} />
              Missing
            </span>
          )}
          {saved && (
            <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
              <CheckCircle2 size={12} />
              Saved
            </span>
          )}
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <Pencil size={14} />
            </button>
          ) : (
            <button
              onClick={() => setEditing(false)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Static display */}
      {!editing && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-0.5">
          {supplier.address && (
            <p className="text-xs text-gray-500">{supplier.address}</p>
          )}
          {supplier.phone && (
            <p className="text-xs text-gray-500">{supplier.phone}</p>
          )}
          {supplier.email && (
            <p className="text-xs text-gray-500">{supplier.email}</p>
          )}
          {!supplier.address && !supplier.phone && !supplier.email && (
            <p className="text-xs text-gray-400 italic">No contact details — click edit to add</p>
          )}
        </div>
      )}

      {/* Editable form */}
      {editing && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {(
            [
              ["address",      "Address"],
              ["phone",        "Phone"],
              ["email",        "Email"],
              ["contact_name", "Contact name"],
            ] as [keyof typeof form, string][]
          ).map(([field, label]) => (
            <div key={field} className={field === "address" ? "col-span-2" : ""}>
              <label className="block text-xs text-gray-500 mb-0.5">{label}</label>
              <input
                value={form[field]}
                onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
          ))}
          <div className="col-span-2 flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 text-sm bg-indigo-600 text-white px-4 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              <Check size={14} />
              {saving ? "Saving…" : "Save to DB"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
