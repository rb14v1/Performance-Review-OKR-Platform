import { apiClient } from "../client";
import type { User } from "../../types";

export async function login(email: string, password: string) {
  const response = await apiClient.post("/auth/login/", { email, password });
  return response.data as { access: string; refresh: string };
}

export async function fetchMe() {
  const response = await apiClient.get("/auth/me/");
  return response.data as User;
}
