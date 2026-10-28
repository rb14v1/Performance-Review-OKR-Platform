import { apiClient } from "../client";
import type { OrgProgressRow, TeamProgressRow } from "../../types";

export async function fetchTeamProgress(cycleId?: number) {
  const response = await apiClient.get<{ results: TeamProgressRow[] }>("/dashboard/team-progress/", {
    params: cycleId ? { cycle: cycleId } : undefined,
  });
  return response.data.results;
}

export async function fetchOrgProgress(cycleId?: number) {
  const response = await apiClient.get<{ results: OrgProgressRow[] }>("/dashboard/org-progress/", {
    params: cycleId ? { cycle: cycleId } : undefined,
  });
  return response.data.results;
}
