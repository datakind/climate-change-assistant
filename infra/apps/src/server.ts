import { join } from "path";
import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";

import { rootDir, stackName } from "./constants";
import { config } from "./config";
import { createDefaultECSRoles } from "./utils";

const assistantResource = `${stackName}-chat`;

const repository = new awsx.ecr.Repository(assistantResource, {
  imageScanningConfiguration: {
    scanOnPush: true,
  },
  lifecyclePolicy: {
    rules: [{ maximumAgeLimit: 14, tagStatus: "untagged" }],
  },
});

const image = new awsx.ecr.Image(`${assistantResource}-image`, {
  repositoryUrl: repository.url,
  context: join(rootDir, "app"),
  platform: "linux/amd64",
});

const { task, execution } = createDefaultECSRoles(assistantResource);

const logGroup = new aws.cloudwatch.LogGroup(assistantResource, {
  retentionInDays: 1,
});

const service = new awsx.ecs.FargateService(assistantResource, {
  cluster: config.appClusterId,
  networkConfiguration: {
    subnets: config.privateSubnetIds,
    securityGroups: [
      config.vpcHttpSecurityGroupId,
      config.publicHttpSecurityGroupId,
    ],
    assignPublicIp: false,
  },
  taskDefinitionArgs: {
    taskRole: {
      roleArn: task.role.arn,
    },
    executionRole: {
      roleArn: execution.role.arn,
    },
    container: {
      name: assistantResource,
      image: image.imageUri,
      secrets: [],
      environment: [
        { name: "CLIENT_ID", value: config.assistantApiAuthClientId },
        { name: "CLIENT_SECRET", value: config.assistantApiAuthClientSecret },
        { name: "MODEL", value: config.model },
        { name: "OPENAI_API_KEY", value: config.openApiKey },
        { name: "OAUTH_AUTH0_CLIENT_ID", value: config.assistantAuthClientId },
        {
          name: "OAUTH_AUTH0_CLIENT_SECRET",
          value: config.assistantAuthClientSecret,
        },
        { name: "OAUTH_AUTH0_DOMAIN", value: config.oAuthAuth0Domain },
        { name: "CHAINLIT_AUTH_SECRET", value: config.chainlitAuthSecret },
        { name: "PF_API_URL", value: config.authApiUrl },
        { name: "PF_TOKEN_AUDIENCE", value: config.authTokenAudience },
        { name: "PF_TOKEN_URL", value: config.authTokenUrl },
      ],
      portMappings: [
        {
          targetGroup: config.assistantTargetGroup,
        },
      ],
      logConfiguration: {
        logDriver: "awslogs",
        options: {
          "awslogs-group": logGroup.name,
          "awslogs-region": aws.config.region,
          "awslogs-stream-prefix": "ecs",
        },
      },
    },
    cpu: config.server.cpu,
    memory: config.server.memory,
  },
  desiredCount: 1,
});

export const serverFargateServiceUrn = service.urn;
export const serverFargateServiceName = service.service.name;
