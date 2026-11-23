terraform {
    required_version = ">= 1.5.0"

    required_providers {
        azurerm = {
            source  = "hashicorp/azurerm"
            version = "~> 4.0"
        }
    }

    backend "azurerm" {
        resource_group_name  = "tfstate-rg"
        storage_account_name = "tfstatepalm674201"
        container_name       = "tfstate"
        key                  = "dev.terraform.tfstate"
    }
}

provider "azurerm" {
    features {}
    subscription_id = var.azure_subscription_id
}

module "azure" {
    source = "../azure"

    backend_api_url = var.backend_api_url
}