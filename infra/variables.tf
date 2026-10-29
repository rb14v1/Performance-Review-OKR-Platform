variable "resource_group_name" {
  description = "Name of the Azure Resource Group that hosts all platform resources."
  type        = string
}

variable "location" {
  description = "Primary Azure region for the resource group (e.g. eastus2)."
  type        = string
  default     = "eastus2"
}

variable "postgres_admin_login" {
  description = "Administrator login name for the PostgreSQL Flexible Server."
  type        = string
  sensitive   = true
}

variable "postgres_admin_password" {
  description = "Administrator password for the PostgreSQL Flexible Server."
  type        = string
  sensitive   = true
}

variable "postgres_sku_name" {
  description = "SKU name for the PostgreSQL Flexible Server (e.g. GP_Standard_D2s_v3)."
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "postgres_version" {
  description = "PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "tags" {
  description = "Map of tags applied to all resources."
  type        = map(string)
  default     = {}
}
