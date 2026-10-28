import { useEffect, useState } from "react";
import { listCycles } from "../api/endpoints/reviews";
import type { ReviewCycle } from "../types";

/** Shared "which cycle am I looking at" selection, defaulting to the most
 * recently created cycle. Used across the OKR, review and dashboard pages
 * so they stay in sync without a heavier global store. */
export function useSelectedCycle() {
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listCycles()
      .then((data) => {
        setCycles(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const selected = cycles.find((c) => c.id === selectedId) || null;

  return { cycles, selected, selectedId, setSelectedId, loading, setCycles };
}
