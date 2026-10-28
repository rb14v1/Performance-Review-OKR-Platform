import { apiClient } from "../client";
import type { Paginated, User } from "../../types";

export async function listUsers() {
  const response = await apiClient.get<Paginated<User> | User[]>("/users/");
  return response.data;
}

export async function listDirectReports() {
  const response = await apiClient.get<Paginated<User> | User[]>("/users/direct-reports/");
  return response.data;
}

export async function listOrgTree() {
  const response = await apiClient.get<User[]>("/users/org-tree/");
  return response.data;
}
