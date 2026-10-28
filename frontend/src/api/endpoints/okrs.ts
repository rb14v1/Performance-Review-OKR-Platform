import { apiClient } from "../client";
import type { CheckIn, KeyResult, Objective, Paginated } from "../../types";

function unwrap<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listObjectives(cycleId?: number) {
  const response = await apiClient.get<Paginated<Objective> | Objective[]>("/objectives/", {
    params: cycleId ? { cycle: cycleId } : undefined,
  });
  return unwrap(response.data);
}

export async function getObjective(id: number) {
  const response = await apiClient.get<Objective>(`/objectives/${id}/`);
  return response.data;
}

export async function createObjective(payload: {
  cycle: number;
  title: string;
  description?: string;
  parent_objective?: number | null;
}) {
  const response = await apiClient.post<Objective>("/objectives/", payload);
  return response.data;
}

export async function createKeyResult(payload: {
  objective: number;
  title: string;
  metric_type: string;
  start_value: number;
  target_value: number;
  current_value: number;
  weight?: number | null;
}) {
  const response = await apiClient.post<KeyResult>("/key-results/", payload);
  return response.data;
}

export async function createCheckIn(payload: {
  key_result: number;
  value: number;
  confidence_level: string;
  comment?: string;
}) {
  const response = await apiClient.post<CheckIn>("/check-ins/", payload);
  return response.data;
}
