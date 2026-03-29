"use client";

import { useState } from "react";
import { Plane, MapPin, Users, Building2, Calendar } from "lucide-react";
import clsx from "clsx";
import type { ADSDocument, SupplierRecord } from "@/types/ads";
import SupplierRow from "./SupplierRow";

interface Props {
  document: ADSDocument;
  onSupplierSaved: () => void;
}

type Tab = "overview" | "itinerary" | "flights" | "suppliers";

const TABS: { id: Tab; label: string; Icon: React.ElementType }[] = [
  { id: "overview",   label: "Overview",   Icon: Users },
  { id: "itinerary",  label: "Itinerary",  Icon: Calendar },
  { id: "flights",    label: "Flights",    Icon: Plane },
  { id: "suppliers",  label: "Suppliers",  Icon: Building2 },
];

const CATEGORY_ICONS: Record<string, string> = {
  Flight: "✈", Transfer: "🚌", Sightseeing: "🗺",
  Meal: "🍽", "Hotel Check-in": "🏨", "Hotel Check-out": "🏨",
  Shopping: "🛍", Activity: "⚡", Other: "•",
};

export default function ParseResults({ document: doc, onSupplierSaved }: Props) {
  const [tab, setTab] = useState<Tab>("overview");
  const [suppliers, setSuppliers] = useState<SupplierRecord[]>(doc.suppliers);

  const missing = suppliers.filter((s) => s.status === "missing").length;
  const gi = doc.group_info;
  const px = doc.pax_details;

  return (
    <div className="flex flex-col gap-6">
      {/* Tab bar */}
      <div className="flex gap-1 bg-white border border-gray-100 rounded-xl p-1 w-fit">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              tab === id
                ? "bg-indigo-600 text-white"
                : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
            )}
          >
            <Icon size={14} />
            {label}
            {id === "suppliers" && missing > 0 && (
              <span className="bg-amber-400 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                {missing}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {tab === "overview" && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Group code",    value: gi.group_code },
            { label: "Tour",          value: gi.tour_name },
            { label: "Destination",   value: gi.destination ?? "—" },
            { label: "Total days",    value: `${gi.total_days} days` },
            { label: "Departure",     value: gi.departure_date },
            { label: "Return",        value: gi.return_date },
            { label: "Total pax",     value: String(px.total_pax) },
            { label: "Room config",   value: Object.entries(px.room_config).filter(([,v]) => v > 0).map(([k,v]) => `${v}×${k}`).join("  ") || "—" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white border border-gray-100 rounded-xl p-4">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className="text-sm font-medium text-gray-900 break-words">{value}</p>
            </div>
          ))}

          {px.upgrade_notes.length > 0 && (
            <div className="col-span-2 sm:col-span-4 bg-indigo-50 border border-indigo-100 rounded-xl p-4">
              <p className="text-xs text-indigo-500 mb-1 font-medium uppercase tracking-wide">Upgrade notes</p>
              <ul className="flex flex-col gap-1">
                {px.upgrade_notes.map((n, i) => (
                  <li key={i} className="text-sm text-indigo-800">• {n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── ITINERARY ── */}
      {tab === "itinerary" && (
        <div className="flex flex-col gap-4">
          {doc.daily_itinerary.map((day) => (
            <div key={day.day_number} className="bg-white border border-gray-100 rounded-xl overflow-hidden">
              {/* Day header */}
              <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <span className="w-7 h-7 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
                    {day.day_number}
                  </span>
                  <div>
                    <p className="font-medium text-sm text-gray-900">{day.day_title ?? `Day ${day.day_number}`}</p>
                    <p className="text-xs text-gray-400">{day.date}</p>
                  </div>
                </div>
                {day.hotel && (
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <MapPin size={12} />
                    {day.hotel}
                  </div>
                )}
              </div>

              {/* Meals pill row */}
              {day.meals && (
                <div className="px-5 py-2 flex gap-2 border-b border-gray-50">
                  {(["breakfast", "lunch", "dinner"] as const).map((m) => (
                    <span
                      key={m}
                      className={clsx(
                        "text-xs px-2.5 py-0.5 rounded-full border capitalize",
                        day.meals?.[m]
                          ? "bg-green-50 text-green-700 border-green-100"
                          : "bg-gray-50 text-gray-400 border-gray-100"
                      )}
                    >
                      {m.charAt(0).toUpperCase() + m.slice(1)}{" "}
                      {day.meals?.[m] ? "✓" : "—"}
                    </span>
                  ))}
                </div>
              )}

              {/* Activities */}
              <div className="divide-y divide-gray-50">
                {day.activities.map((act, i) => (
                  <div key={i} className="flex gap-3 px-5 py-3">
                    <span className="text-base shrink-0 w-5 text-center mt-0.5">
                      {CATEGORY_ICONS[act.category] ?? "•"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">{act.description_en}</p>
                      {act.description_zh && (
                        <p className="text-xs text-gray-400 mt-0.5">{act.description_zh}</p>
                      )}
                      {act.supplier_ref && (
                        <p className="text-xs text-indigo-500 mt-0.5">{act.supplier_ref}</p>
                      )}
                    </div>
                    {act.time && (
                      <span className="text-xs text-gray-400 shrink-0 font-mono">{act.time}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── FLIGHTS ── */}
      {tab === "flights" && (
        <div className="flex flex-col gap-3">
          {doc.flights.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No flights extracted.</p>
          ) : (
            doc.flights.map((fl, i) => (
              <div key={i} className="bg-white border border-gray-100 rounded-xl px-5 py-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                  <Plane size={18} className="text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-gray-900">{fl.flight_number}</span>
                    {fl.airline && <span className="text-xs text-gray-400">{fl.airline}</span>}
                    <span className="text-xs bg-gray-50 border border-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                      Day {fl.day_number}
                    </span>
                    {fl.overnight_flight && (
                      <span className="text-xs bg-indigo-50 text-indigo-600 border border-indigo-100 px-2 py-0.5 rounded-full">
                        Overnight
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm font-mono font-medium">{fl.origin_iata}</span>
                    <span className="text-gray-300">→</span>
                    <span className="text-sm font-mono font-medium">{fl.dest_iata}</span>
                    <span className="text-xs text-gray-400">{fl.origin_city} → {fl.dest_city}</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-gray-500">{fl.departure_datetime}</p>
                  <p className="text-xs text-gray-400">→ {fl.arrival_datetime}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── SUPPLIERS ── */}
      {tab === "suppliers" && (
        <div className="flex flex-col gap-2">
          {suppliers.map((s, i) => (
            <SupplierRow
              key={s.supplier_id ?? i}
              supplier={s}
              onSaved={(updated) =>
                setSuppliers((prev) =>
                  prev.map((x) => (x.supplier_id === updated.supplier_id ? updated : x))
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
