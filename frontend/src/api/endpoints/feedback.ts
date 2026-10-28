import { apiClient } from "../client";
import type {
  CalibrationEntry,
  CalibrationSession,
  FeedbackRequest,
  Paginated,
  PeerFeedback,
} from "../../types";

function unwrap<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listFeedbackRequests() {
  const response = await apiClient.get<Paginated<FeedbackRequest> | FeedbackRequest[]>(
    "/feedback-requests/"
  );
  return unwrap(response.data);
}

export async function createFeedbackRequest(payload: {
  cycle: number;
  subject: number;
  reviewer: number;
  relationship: string;
}) {
  const response = await apiClient.post<FeedbackRequest>("/feedback-requests/", payload);
  return response.data;
}

export async function respondToFeedbackRequest(id: number, accept: boolean) {
  const response = await apiClient.post<FeedbackRequest>(`/feedback-requests/${id}/respond/`, {
    accept,
  });
  return response.data;
}

export async function submitPeerFeedback(payload: {
  cycle: number;
  subject: number;
  relationship: string;
  anonymity_mode: string;
  strengths: string;
  improvements: string;
  feedback_request?: number;
}) {
  const response = await apiClient.post<PeerFeedback>("/peer-feedback/", payload);
  return response.data;
}

export async function listPeerFeedbackFor(subjectId: number, cycleId: number) {
  const response = await apiClient.get<Paginated<PeerFeedback> | PeerFeedback[]>("/peer-feedback/", {
    params: { subject: subjectId, cycle: cycleId },
  });
  return unwrap(response.data);
}

export async function listCalibrationSessions(cycleId?: number) {
  const response = await apiClient.get<Paginated<CalibrationSession> | CalibrationSession[]>(
    "/calibration-sessions/",
    { params: cycleId ? { cycle: cycleId } : undefined }
  );
  return unwrap(response.data);
}

export async function createCalibrationSession(payload: { cycle: number; department_id: number }) {
  const response = await apiClient.post<CalibrationSession>("/calibration-sessions/", payload);
  return response.data;
}

export async function createCalibrationEntry(payload: {
  session: number;
  employee_id: number;
  pre_rating: string;
}) {
  const response = await apiClient.post<CalibrationEntry>("/calibration-entries/", payload);
  return response.data;
}

export async function adjustCalibrationEntry(id: number, postRating: string, reason: string) {
  const response = await apiClient.post<CalibrationEntry>(`/calibration-entries/${id}/adjust/`, {
    post_rating: postRating,
    adjustment_reason: reason,
  });
  return response.data;
}
