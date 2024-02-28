import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

import { config } from "../config";

const customOriginDefaults = {
  httpPort: 80,
  httpsPort: 443,
  originSslProtocols: ["SSLv3"],
  originProtocolPolicy: "https-only",
};

type DefaultCacheBehavior = pulumi.Unwrap<
  aws.cloudfront.DistributionArgs["defaultCacheBehavior"]
>;
export type ForwardedValues = DefaultCacheBehavior["forwardedValues"];

type CustomOriginConfig = {
  httpPort: number;
  httpsPort: number;
  originSslProtocols: string[];
  originProtocolPolicy: string;
  originReadTimeout?: number;
};

export interface CreateDistributionArgs {
  allowedMethods: string[];
  cachedMethods: string[];
  domainAlias: pulumi.Input<string>;
  forward?: ForwardedValues;
  origin: { target: aws.lb.LoadBalancer };
  originReadTimeout?: number;
  webAclId?: pulumi.Output<any>;
  tags?: any;
}

export function createDistribution(name: string, args: CreateDistributionArgs) {
  const { webAclId, tags, allowedMethods, cachedMethods, originReadTimeout } =
    args;
  let customErrorResponses: aws.cloudfront.DistributionArgs["customErrorResponses"];
  let customOriginConfig: CustomOriginConfig | undefined = customOriginDefaults;
  let domainName: pulumi.Output<string> = args.origin.target.dnsName;
  let originId: pulumi.Output<string> = args.origin.target.name;

  customOriginConfig.originReadTimeout = originReadTimeout || 30;

  return new aws.cloudfront.Distribution(name, {
    aliases: [args.domainAlias],
    defaultCacheBehavior: {
      compress: true,
      forwardedValues: args.forward ?? {
        cookies: { forward: "none" },
        queryString: false,
      },
      targetOriginId: originId,
      viewerProtocolPolicy: "redirect-to-https",
      allowedMethods,
      cachedMethods,
    },
    enabled: true,
    origins: [{ customOriginConfig, domainName, originId }],
    restrictions: {
      geoRestriction: {
        restrictionType: "none",
      },
    },
    viewerCertificate: {
      acmCertificateArn: config.ssl.usEast1.arn,
      minimumProtocolVersion: "TLSv1.2_2019",
      sslSupportMethod: "sni-only",
    },
    customErrorResponses,
    webAclId,
    tags,
  });
}
