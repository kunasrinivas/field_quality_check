# Infrastructure Automation for Telecom Application

This project contains Bicep templates and CI/CD pipelines to automate the deployment of infrastructure for a GDPR-compliant telecom contractor work review system.

## Files Overview

### **Infrastructure (Bicep Templates)**
1. `infra/resource_group.bicep`
   - Creates the resource group for all resources.
   - Defaults to the `westeurope` region for GDPR compliance.

2. `infra/keyvault.bicep`
   - Provisions an Azure Key Vault for securely managing secrets.
   - Includes soft delete with a 90-day retention policy (GDPR requirement).

### **GitHub Actions Pipeline**
- `.github/workflows/deploy_infrastructure.yml`
  - Automates deployment of the resource group and Key Vault using Bicep templates.
  - Secrets for Azure authentication are securely configured in GitHub Secrets.

### **Destroy Script**
- `scripts/destroy_infra.sh`
  - Deletes the resource group and all associated resources for quick iteration.
  - Avoids resource sprawl in development/testing.

### **How to Deploy**
1. Ensure Azure CLI and access to the subscription.
2. Push changes to the `main` branch to trigger the deployment.
3. Use the GitHub Actions pipeline for automated provisioning.

### **How to Destroy Resources**
Run the following script:
```bash
bash scripts/destroy_infra.sh
```

### **Future Enhancements**
- Add other resources (e.g., Storage, SQL, AI Models) incrementally.