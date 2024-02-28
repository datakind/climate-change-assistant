import * as pulumi from "@pulumi/pulumi";

import { config as pulumiConfig, stackName } from "./constants";

const foundationResources = new pulumi.StackReference(
  `Probable-Futures/foundation/${stackName}`
);
const servicesStackRef = new pulumi.StackReference(
  `Probable-Futures/services/${stackName}`
);

const assistantServicesStackRef = new pulumi.StackReference(
  `Probable-Futures/assistant-services/${stackName}`
);

const servicesOutput = (outputName: string) =>
  servicesStackRef.requireOutput(outputName);

const foundationOutput = (outputName: string) =>
  foundationResources.requireOutput(outputName);

const assistantServicesOutput = (outputName: string) =>
  assistantServicesStackRef.requireOutput(outputName);

interface TaskConfig {
  cpu: string;
  memory: string;
}

const serverConfig = pulumiConfig.requireObject<TaskConfig>("serverTask");

export const config = {
  server: {
    cpu: serverConfig.cpu,
    memory: serverConfig.memory,
  },
  appClusterId: servicesOutput("appClusterId"),
  publicHttpSecurityGroupId: foundationOutput("publicHttpSecurityGroupId"),
  privateSubnetIds: foundationOutput("privateSubnetIds"),
  vpcHttpSecurityGroupId: foundationOutput("vpcHttpSecurityGroupId"),
  assistantAuthClientId: assistantServicesOutput("assistantAuthClientId"),
  assistantAuthClientSecret: assistantServicesOutput(
    "assistantAuthClientSecret"
  ),
  assistantApiAuthClientId: assistantServicesOutput("assistantApiAuthClientId"),
  assistantApiAuthClientSecret: assistantServicesOutput(
    "assistantApiAuthClientSecret"
  ),
  assistantTargetGroup: assistantServicesOutput("assistantTargetGroup"),
  assistantId: pulumiConfig.requireSecret("assistantId"),
  model: pulumiConfig.require("model"),
  openApiKey: pulumiConfig.requireSecret("openApiKey"),
  oAuthAuth0Domain: pulumiConfig.require("oAuthAuth0Domain"),
  chainlitAuthSecret: pulumiConfig.requireSecret("chainlitAuthSecret"),
  authApiUrl: pulumiConfig.require("authApiUrl"),
  authTokenAudience: pulumiConfig.require("authTokenAudience"),
  authTokenUrl: pulumiConfig.require("authTokenUrl"),
};
