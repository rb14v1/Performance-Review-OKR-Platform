# Serves components: backend-api, web
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  # Backend config supplied at init time via -backend-config flags (storage account/container/key
  # are resolved per app+environment by DEPLOY, not hardcoded here) — see lib/terraform-apply.ts.
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}


resource "azurerm_postgresql_flexible_server" "postgresql" {
  name                   = "psql-performence-test-5"
  resource_group_name    = "performence-test-5"
  location               = "uksouth"
  version                = "16"
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  administrator_login    = "psqladmin"
  administrator_password = random_password.postgresql_admin.result
  public_network_access_enabled = false

  # Azure assigns an availability zone on creation since none is declared here — a later apply
  # then sees that as drift and tries to reset it, which the provider rejects outright:
  # "zone can only be changed when exchanged with the zone specified in
  # high_availability.0.standby_availability_zone". Observed on prompt-lib-test-10, blocking every
  # apply after the first. Ignoring drift on the attribute this config never set an opinion on is
  # correct, not a workaround — the alternative is declaring an explicit zone, which would make a
  # dev-tier single-app server fail to provision at all if that zone has no capacity.
  lifecycle {
    ignore_changes = [zone]
  }
}

resource "random_password" "postgresql_admin" {
  length  = 24
  special = true
}

data "azurerm_private_dns_zone" "postgresql_dns_zone" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = var.hub_resource_group
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgresql_dns_zone_link" {
  name                  = "link-performence-test-5"
  resource_group_name   = var.hub_resource_group
  private_dns_zone_name = data.azurerm_private_dns_zone.postgresql_dns_zone.name
  virtual_network_id    = var.vnet_id
}

resource "azurerm_private_endpoint" "postgresql_pe" {
  name                = "pe-psql-performence-test-5"
  resource_group_name = "performence-test-5"
  location            = "uksouth"
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psql-privateserviceconnection"
    private_connection_resource_id = azurerm_postgresql_flexible_server.postgresql.id
    subresource_names              = ["postgresqlServer"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "psql-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.postgresql_dns_zone.id]
  }
}

resource "azurerm_redis_cache" "redis" {
  name                = "redis-performence-test-5"
  resource_group_name = "performence-test-5"
  location            = "uksouth"
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  non_ssl_port_enabled = false
  minimum_tls_version = "1.2"
  public_network_access_enabled = false
}

data "azurerm_private_dns_zone" "redis_dns_zone" {
  name                = "privatelink.redis.cache.windows.net"
  resource_group_name = var.hub_resource_group
}

resource "azurerm_private_dns_zone_virtual_network_link" "redis_dns_zone_link" {
  name                  = "link-performence-test-5"
  resource_group_name   = var.hub_resource_group
  private_dns_zone_name = data.azurerm_private_dns_zone.redis_dns_zone.name
  virtual_network_id    = var.vnet_id
}

resource "azurerm_private_endpoint" "redis_pe" {
  name                = "pe-redis-performence-test-5"
  resource_group_name = "performence-test-5"
  location            = "uksouth"
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "redis-privateserviceconnection"
    private_connection_resource_id = azurerm_redis_cache.redis.id
    subresource_names              = ["redisCache"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "redis-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.redis_dns_zone.id]
  }
}