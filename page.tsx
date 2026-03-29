"use client";

import { useState } from "react";
import type { ADSDocument, ParseResponse } from "@/types/ads";
import { parseDocx } from "@/lib/api";
import UploadZone from "@/components/UploadZone";
import ParseResults from "@/components/ParseResults";
import WarningBanner from "@/components/WarningBanner";

type Stage = "idle" | "parsing" | "done" | "error";

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<ADSDocument | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [missingCount, setMissingCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");

  async function handleFile(file: File, apiKey: string) {
    setStage("parsing");
    setErrorMsg("");
    try {
      const res: ParseResponse = await parseDocx(file, apiKey);
      if (!res.success || !res.data) throw new Error(res.error ?? "Unknown error");
      setResult(res.data);
      setWarnings(res.warnings);
      setMissingCount(res.missing_suppliers);
      setStage("done");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : String(e));
      setStage("error");
    }
  }

  function reset() {
    setStage("idle");
    setResult(null);
    setWarnings([]);
    setMissingCount(0);
    setErrorMsg("");
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">A</span>
          </div>
          <span className="font-semibold text-gray-900">ADS Parser</span>
          <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-100">
            v1.0
          </span>
        </div>
        {stage === "done" && (
          <button
            onClick={reset}
            className="text-sm text-gray-500 hover:text-gray-900 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
          >
            ← New document
          </button>
        )}
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* Warnings banner */}
        {stage === "done" && (missingCount > 0 || warnings.length > 0) && (
          <WarningBanner
            missingCount={missingCount}
            warnings={warnings}
            className="mb-6"
          />
        )}

        {stage === "idle" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <h1 className="text-2xl font-semibold text-gray-900 mb-2">
              Chinese itinerary → ADS document
            </h1>
            <p className="text-gray-500 mb-8 text-center max-w-md">
              Upload a Word (.docx) tour itinerary in Chinese. The parser extracts
              flights, daily activities, and supplier details automatically.
            </p>
            <UploadZone onSubmit={handleFile} />
          </div>
        )}

        {stage === "parsing" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
            <p className="text-gray-600 text-sm">Parsing document with Claude…</p>
          </div>
        )}

        {stage === "error" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-lg w-full text-center">
              <p className="text-red-700 font-medium mb-1">Parse failed</p>
              <p className="text-red-600 text-sm">{errorMsg}</p>
              <button
                onClick={reset}
                className="mt-4 text-sm text-red-700 border border-red-200 rounded-lg px-4 py-2 hover:bg-red-100 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {stage === "done" && result && (
          <ParseResults document={result} onSupplierSaved={() => {}} />
        )}
      </main>
    </div>
  );
}
