# Hosts the Streamlit dashboard as an Azure Container App.
#
# Terraform provisions the registry and the app, but it does not build or
# push the image - before the first apply succeeds, build and push the
# streamlit/ image to the ACR this creates, e.g.:
#   az acr build --registry <acr_name> --image palm-streamlit:latest ./streamlit

variable "backend_api_url" {
  description = "Full URL the dashboard calls for sensor events, e.g. https://<backend-host>/events/latest"
  type        = string
}

# Globally unique across all of Azure, alphanumeric only - rename if taken.
resource "azurerm_container_registry" "frontend_acr" {
  name                = "palmprofrontendacr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_log_analytics_workspace" "frontend_logs" {
  name                = "palmpro-frontend-logs"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "frontend_env" {
  name                       = "palmpro-frontend-env"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.frontend_logs.id
}

# Created and granted AcrPull before the Container App exists, so the first
# image pull doesn't race the role assignment.
resource "azurerm_user_assigned_identity" "frontend_identity" {
  name                = "palmpro-frontend-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}

resource "azurerm_role_assignment" "frontend_acr_pull" {
  scope                = azurerm_container_registry.frontend_acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.frontend_identity.principal_id
}

resource "azurerm_container_app" "frontend" {
  name                         = "palmpro-frontend"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.frontend_env.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.frontend_identity.id]
  }

  registry {
    server   = azurerm_container_registry.frontend_acr.login_server
    identity = azurerm_user_assigned_identity.frontend_identity.id
  }

  template {
    container {
      name   = "streamlit"
      image  = "${azurerm_container_registry.frontend_acr.login_server}/palm-streamlit:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "BACKEND_API_URL"
        value = var.backend_api_url
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  depends_on = [azurerm_role_assignment.frontend_acr_pull]
}
