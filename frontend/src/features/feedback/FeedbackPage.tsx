import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../app/store";
import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { listUsers } from "../../api/endpoints/users";
import {
  createFeedbackRequest,
  listFeedbackRequests,
  listPeerFeedbackFor,
  respondToFeedbackRequest,
  submitPeerFeedback,
} from "../../api/endpoints/feedback";
import { extractErrorMessage } from "../../api/client";
import type { PeerFeedback, Paginated, User } from "../../types";

export default function FeedbackPage() {
  const { user } = useAuth();
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const { data: usersRaw } = useAsync(() => listUsers(), []);
  const allUsers: User[] = usersRaw
    ? Array.isArray(usersRaw)
      ? usersRaw
      : (usersRaw as Paginated<User>).results
    : [];

  const { data: requests, reload: reloadRequests } = useAsync(() => listFeedbackRequests(), []);

  const [subjectId, setSubjectId] = useState("");
  const [reviewerId, setReviewerId] = useState("");
  const [relationship, setRelationship] = useState("peer");
  const [requestError, setRequestError] = useState<string | null>(null);

  const [submissions, setSubmissions] = useState<Record<number, { strengths: string; improvements: string; anonymity: string }>>(
    {}
  );
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [viewSubjectId, setViewSubjectId] = useState("");
  const [viewResult, setViewResult] = useState<PeerFeedback[] | null>(null);
  const [viewMessage, setViewMessage] = useState<string | null>(null);

  async function handleCreateRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setRequestError(null);
    try {
      await createFeedbackRequest({
        cycle: selectedId,
        subject: Number(subjectId),
        reviewer: Number(reviewerId),
        relationship,
      });
      setSubjectId("");
      setReviewerId("");
      reloadRequests();
    } catch (err) {
      setRequestError(extractErrorMessage(err));
    }
  }

  async function handleRespond(id: number, accept: boolean) {
    await respondToFeedbackRequest(id, accept);
    reloadRequests();
  }

  async function handleSubmitFeedback(requestId: number, subjectIdValue: number) {
    const form = submissions[requestId] || { strengths: "", improvements: "", anonymity: "anonymous" };
    setSubmitError(null);
    try {
      await submitPeerFeedback({
        cycle: selectedId!,
        subject: subjectIdValue,
        relationship: "peer",
        anonymity_mode: form.anonymity,
        strengths: form.strengths,
        improvements: form.improvements,
        feedback_request: requestId,
      });
      reloadRequests();
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    }
  }

  async function handleViewFeedback() {
    if (!selectedId || !viewSubjectId) return;
    setViewMessage(null);
    const results = await listPeerFeedbackFor(Number(viewSubjectId), selectedId);
    if (results.length === 0) {
      setViewResult(null);
      setViewMessage(
        "No feedback released yet - either none submitted, or the minimum-reviewer threshold hasn't been met."
      );
    } else {
      setViewResult(results);
    }
  }

  const myPendingRequests = requests?.filter(
    (r) => r.reviewer.id === user?.id && r.status === "pending"
  );
  const myAcceptedRequests = requests?.filter(
    (r) => r.reviewer.id === user?.id && r.status === "accepted"
  );

  return (
    <div>
      <h2>360 Feedback</h2>
      <label>
        Cycle:{" "}
        <select
          value={selectedId ?? ""}
          onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
        >
          {cycles.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.status})
            </option>
          ))}
        </select>
      </label>

      <div className="card">
        <h3>Request feedback for someone</h3>
        <form className="stacked" onSubmit={handleCreateRequest}>
          <label>
            Subject (being reviewed)
            <select required value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
              <option value="">Select...</option>
              {allUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.email}
                </option>
              ))}
            </select>
          </label>
          <label>
            Reviewer
            <select required value={reviewerId} onChange={(e) => setReviewerId(e.target.value)}>
              <option value="">Select...</option>
              {allUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.email}
                </option>
              ))}
            </select>
          </label>
          <label>
            Relationship
            <select value={relationship} onChange={(e) => setRelationship(e.target.value)}>
              <option value="peer">Peer</option>
              <option value="manager">Manager</option>
              <option value="direct_report">Direct report</option>
            </select>
          </label>
          {requestError && <p className="error-text">{requestError}</p>}
          <button type="submit" disabled={!selectedId}>
            Send request
          </button>
        </form>
      </div>

      <div className="card">
        <h3>Requests waiting on you</h3>
        {myPendingRequests?.map((r) => (
          <div key={r.id} style={{ marginBottom: "0.5rem" }}>
            Give {r.relationship} feedback for <strong>{r.subject.email}</strong>{" "}
            <button onClick={() => handleRespond(r.id, true)}>Accept</button>{" "}
            <button className="secondary" onClick={() => handleRespond(r.id, false)}>
              Decline
            </button>
          </div>
        ))}
        {(!myPendingRequests || myPendingRequests.length === 0) && (
          <p className="muted">Nothing pending.</p>
        )}
      </div>

      <div className="card">
        <h3>Feedback to submit</h3>
        {myAcceptedRequests?.map((r) => {
          const form = submissions[r.id] || { strengths: "", improvements: "", anonymity: "anonymous" };
          return (
            <div key={r.id} className="card" style={{ background: "#fafbfc" }}>
              <strong>{r.subject.email}</strong>
              <label>
                Strengths
                <textarea
                  value={form.strengths}
                  onChange={(e) =>
                    setSubmissions((prev) => ({ ...prev, [r.id]: { ...form, strengths: e.target.value } }))
                  }
                />
              </label>
              <label>
                Areas to improve
                <textarea
                  value={form.improvements}
                  onChange={(e) =>
                    setSubmissions((prev) => ({ ...prev, [r.id]: { ...form, improvements: e.target.value } }))
                  }
                />
              </label>
              <label>
                Anonymity
                <select
                  value={form.anonymity}
                  onChange={(e) =>
                    setSubmissions((prev) => ({ ...prev, [r.id]: { ...form, anonymity: e.target.value } }))
                  }
                >
                  <option value="anonymous">Anonymous</option>
                  <option value="named">Named</option>
                </select>
              </label>
              <button onClick={() => handleSubmitFeedback(r.id, r.subject.id)}>Submit feedback</button>
            </div>
          );
        })}
        {submitError && <p className="error-text">{submitError}</p>}
        {(!myAcceptedRequests || myAcceptedRequests.length === 0) && (
          <p className="muted">Nothing to submit right now.</p>
        )}
      </div>

      <div className="card">
        <h3>View received feedback</h3>
        <p className="muted">
          Released only once at least 3 reviewers have submitted for this subject+cycle, to avoid
          de-anonymizing a small pool. Identities are hidden unless the entry is named or you are HR.
        </p>
        <label>
          Subject user ID (yourself, or your direct report if you're their manager)
          <input value={viewSubjectId} onChange={(e) => setViewSubjectId(e.target.value)} />
        </label>
        <button onClick={handleViewFeedback}>Load feedback</button>
        {viewMessage && <p className="muted">{viewMessage}</p>}
        {viewResult?.map((pf) => (
          <div key={pf.id} className="card" style={{ background: "#fafbfc" }}>
            <p className="badge">{pf.reviewer ? pf.reviewer.email : "Anonymous"}</p>
            <p>
              <strong>Strengths:</strong> {pf.strengths}
            </p>
            <p>
              <strong>Improvements:</strong> {pf.improvements}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
