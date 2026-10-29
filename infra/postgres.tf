# ---------------------------------------------------------------------------
# Azure Database for PostgreSQL Flexible Server
# Backup policy: geo-redundant, 30-day retention, PITR enabled.
# Resource name matches the platform convention:
#   psql-performance-review-okr-platform
# ---------------------------------------------------------------------------

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-performance-review-okr-platform"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location

  version                = var.postgres_version
  administrator_login    = var.postgres_admin_login
  administrator_password = var.postgres_admin_password

  sku_name   = var.postgres_sku_name
  storage_mb = 32768

  # ── Backup & Recovery ──────────────────────────────────────────────────
  # backup_retention_days: 30-day minimum per compliance requirement
  backup_retention_days        = 30
  # geo_redundant_backup_enabled: backups stored in a paired Azure region,
  # satisfying the "separate region" requirement.
  geo_redundant_backup_enabled = true

  # Point-in-time recovery (PITR) is enabled automatically on Flexible Server
  # when backup_retention_days > 0. No additional flag is required.
  # ── End Backup & Recovery ───────────────────────────────────────────────

  tags = merge(var.tags, {
    application = "performance-review-okr-platform"
    managed_by  = "terraform"
  })

  lifecycle {
    # Prevent accidental destruction of the production database.
    prevent_destroy = true
  }
}

# Database for the application
resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "perf_okr_platform"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Firewall rule: allow Azure services (e.g. App Service / AKS) to connect.
# Replace / extend with specific subnet delegations for production.
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ── Outputs ───────────────────────────────────────────────────────────────
output "postgres_server_fqdn" {
  description = "Fully-qualified domain name of the PostgreSQL server."
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_server_name" {
  description = "Name of the PostgreSQL Flexible Server resource."
  value       = azurerm_postgresql_flexible_server.main.name
}
