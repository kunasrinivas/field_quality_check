#!/bin/bash

# Destroy resources created in the subscription
RESOURCE_GROUP="FQCT-ResourceGroup"

# Delete the resource group and all associated resources
az group delete \
  --name $RESOURCE_GROUP \
  --yes \
  --no-wait