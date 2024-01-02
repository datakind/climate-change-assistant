import { join } from "path";
import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

import { createBaseConfig, BaseConfig } from "./utils";

const rootDir = join(__dirname, "..", "..", "..");
const baseConfig = createBaseConfig();
const { pulumiConfig, stackName } = baseConfig;

const identityResources = new pulumi.StackReference(
  `Probable-Futures/identity/global`
);
const foundationResources = new pulumi.StackReference(
  `Probable-Futures/foundation/${stackName}`
);

interface Auth0Config {
  googleConnectionId: string;
}

interface ApiConfig {
  port: number;
  elbAccessLogs: {
    enabled: boolean;
    interval: number;
  };
}

interface SslConf {
  usEast1: pulumi.Output<pulumi.UnwrappedObject<aws.acm.GetCertificateResult>>;
  usWest2: pulumi.Output<pulumi.UnwrappedObject<aws.acm.GetCertificateResult>>;
}

interface ServicesConfig extends BaseConfig {
  environmentLogsBucketId: pulumi.Output<any>;
  ssl: SslConf;
  publicEgressSecurityGroupId: pulumi.Output<any>;
  publicHttpSecurityGroupId: pulumi.Output<any>;
  vpc: {
    publicSubnetIds: pulumi.Output<any>;
    id: pulumi.Output<any>;
  };
  route53ZoneId: pulumi.Output<any>;
  rootDir: string;
  auth0: Auth0Config;
  api: ApiConfig;
}

const usEast1Provider = new aws.Provider(`${stackName}-aws-provider`, {
  region: "us-east-1",
});

const ssl = {
  usEast1: pulumi.output(
    aws.acm.getCertificate(
      {
        domain: "*.probablefutures.org",
        mostRecent: true,
      },
      { provider: usEast1Provider }
    )
  ),
  usWest2: pulumi.output(
    aws.acm.getCertificate({
      domain: "*.probablefutures.org",
      mostRecent: true,
    })
  ),
};

export const config: ServicesConfig = {
  rootDir,
  ssl,
  route53ZoneId: identityResources.requireOutput("route53ZoneId"),
  environmentLogsBucketId: foundationResources.requireOutput(
    "environmentLogsBucketId"
  ),
  publicEgressSecurityGroupId: foundationResources.requireOutput(
    "publicEgressSecurityGroupId"
  ),
  publicHttpSecurityGroupId: foundationResources.requireOutput(
    "publicHttpSecurityGroupId"
  ),
  vpc: {
    publicSubnetIds: foundationResources.requireOutput("publicSubnetIds"),
    id: foundationResources.requireOutput("vpcId"),
  },
  auth0: pulumiConfig.requireObject<Auth0Config>("auth0"),
  api: pulumiConfig.requireObject<ApiConfig>("api"),
  ...baseConfig,
};

export const vpc = aws.ec2.Vpc.get(
  `${baseConfig.stackName}-vpc`,
  config.vpc.id
);
