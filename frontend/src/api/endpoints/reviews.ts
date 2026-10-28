import { apiClient } from "../client";
import type {
  ManagerReview,
  Paginated,
  Rating,
  ReviewCycle,
  SelfReview,
} from "../../types";

function unwrap<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listCycles() {
  const response = await apiClient.get<Paginated<ReviewCycle> | ReviewCycle[]>("/cycles/");
  return unwrap(response.data);
}

export async function createCycle(payload: { name: string; start_date: string; end_date: string }) {
  const response = await apiClient.post<ReviewCycle>("/cycles/", payload);
  return response.data;
}

export async function transitionCycle(id: number, newStatus: string, overrideReason?: string) {
  const response = await apiClient.post<ReviewCycle>(`/cycles/${id}/transition/`, {
    new_status: newStatus,
    override_reason: overrideReason || "",
  });
  return response.data;
}

export async function listSelfReviews(cycleId?: number) {
  const response = await apiClient.get<Paginated<SelfReview> | SelfReview[]>("/self-reviews/", {
    params: cycleId ? { cycle: cycleId } : undefined,
  });
  return unwrap(response.data);
}

export async function createSelfReview(payload: {
  cycle: number;
  accomplishments: string;
  challenges: string;
  self_rating?: string;
}) {
  const response = await apiClient.post<SelfReview>("/self-reviews/", payload);
  return response.data;
}

export async function updateSelfReview(
  id: number,
  payload: { accomplishments: string; challenges: string; self_rating?: string }
) {
  const response = await apiClient.patch<SelfReview>(`/self-reviews/${id}/`, payload);
  return response.data;
}

export async function submitSelfReview(id: number) {
  const response = await apiClient.post<SelfReview>(`/self-reviews/${id}/submit/`);
  return response.data;
}

export async function listManagerReviews(cycleId?: number) {
  const response = await apiClient.get<Paginated<ManagerReview> | ManagerReview[]>(
    "/manager-reviews/",
    { params: cycleId ? { cycle: cycleId } : undefined }
  );
  return unwrap(response.data);
}

export async function createManagerReview(payload: {
  cycle: number;
  employee_id: number;
  draft_rating?: string;
  comments?: string;
}) {
  const response = await apiClient.post<ManagerReview>("/manager-reviews/", payload);
  return response.data;
}

export async function updateManagerReview(
  id: number,
  payload: { draft_rating?: string; comments?: string }
) {
  const response = await apiClient.patch<ManagerReview>(`/manager-reviews/${id}/`, payload);
  return response.data;
}

export async function submitManagerReview(id: number) {
  const response = await apiClient.post<ManagerReview>(`/manager-reviews/${id}/submit/`);
  return response.data;
}

export async function listRatings(cycleId?: number) {
  const response = await apiClient.get<Paginated<Rating> | Rating[]>("/ratings/", {
    params: cycleId ? { cycle: cycleId } : undefined,
  });
  return unwrap(response.data);
}

export async function acknowledgeRating(id: number) {
  const response = await apiClient.post<Rating>(`/ratings/${id}/acknowledge/`);
  return response.data;
}
