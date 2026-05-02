@description('Name of the API Management service (globally unique)')
param apimName string

@description('Azure region')
param location string = 'westeurope'

@description('Publisher email for API Management notifications')
param publisherEmail string

@description('Publisher organisation name')
param publisherName string = 'FQCT Operations'

@description('Hostname of the backend Function App')
param functionAppHostname string

resource apimService 'Microsoft.ApiManagement/service@2022-08-01' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

resource backend 'Microsoft.ApiManagement/service/backends@2022-08-01' = {
  parent: apimService
  name: 'functions-backend'
  properties: {
    description: 'Azure Functions backend for evidence processing'
    url: 'https://${functionAppHostname}/api'
    protocol: 'http'
    tls: {
      validateCertificateChain: true
      validateCertificateName: true
    }
  }
}

resource fqctApi 'Microsoft.ApiManagement/service/apis@2022-08-01' = {
  parent: apimService
  name: 'field-quality-api'
  properties: {
    displayName: 'Field Quality Check API'
    description: 'API for telecom contractor field work evidence submission and status queries'
    apiRevision: '1'
    subscriptionRequired: true
    path: 'fqct'
    protocols: ['https']
    serviceUrl: 'https://${functionAppHostname}/api'
  }
}

resource postEvidenceOp 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  parent: fqctApi
  name: 'post-evidence'
  properties: {
    displayName: 'Submit Evidence'
    method: 'POST'
    urlTemplate: '/evidence'
    description: 'Upload photos or videos as field evidence for a work order'
    request: {
      queryParameters: [
        {
          name: 'workOrderId'
          required: true
          type: 'string'
          description: 'Unique work order identifier'
        }
      ]
    }
    responses: [
      { statusCode: 202, description: 'Evidence accepted for processing' }
      { statusCode: 400, description: 'Bad request — missing required fields' }
    ]
  }
}

resource postInvoiceOp 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  parent: fqctApi
  name: 'post-invoice'
  properties: {
    displayName: 'Submit Invoice'
    method: 'POST'
    urlTemplate: '/invoice'
    description: 'Submit a contractor invoice linked to a work order'
    responses: [
      { statusCode: 202, description: 'Invoice accepted' }
      { statusCode: 400, description: 'Bad request — missing required fields' }
    ]
  }
}

resource getStatusOp 'Microsoft.ApiManagement/service/apis/operations@2022-08-01' = {
  parent: fqctApi
  name: 'get-status'
  properties: {
    displayName: 'Get Decision Status'
    method: 'GET'
    urlTemplate: '/status/{id}'
    templateParameters: [
      {
        name: 'id'
        required: true
        type: 'string'
        description: 'Work order ID'
      }
    ]
    description: 'Retrieve the current AI decision status for a work order'
    responses: [
      { statusCode: 200, description: 'Current status of the work order decision' }
      { statusCode: 404, description: 'Work order not found' }
    ]
  }
}

output apimGatewayUrl string = apimService.properties.gatewayUrl
output apimServiceName string = apimService.name
