import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

import { config } from "../config";

const customOriginDefaults = {
  httpPort: 80,
  httpsPort: 443,
  originSslProtocols: ["SSLv3"],
  originProtocolPolicy: "https-only",
};

type DefaultCacheBehavior = pulumi.Unwrap<aws.cloudfront.DistributionArgs["defaultCacheBehavior"]>;
export type ForwardedValues = DefaultCacheBehavior["forwardedValues"];

type Origin =
  | { target: aws.s3.Bucket; type: "bucket" }
  | { target: aws.s3.Bucket; type: "custom-bucket-endpoint" }
  | { target: aws.lb.LoadBalancer; type: "custom" };

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
  origin: Origin;
  originReadTimeout?: number;
  webAclId?: pulumi.Output<any>;
  tags?: any;
}

export function createDistribution(name: string, args: CreateDistributionArgs) {
  const { webAclId, tags, allowedMethods, cachedMethods, originReadTimeout } = args;
  let customErrorResponses: aws.cloudfront.DistributionArgs["customErrorResponses"];
  let customOriginConfig: CustomOriginConfig | undefined;
  let defaultRootObject: string | undefined;
  let domainName: pulumi.Output<string>;
  let originId: pulumi.Output<string>;

  switch (args.origin.type) {
    case "bucket": {
      customErrorResponses = [{ errorCode: 404, responseCode: 200, responsePagePath: "/" }];
      defaultRootObject = "index.html";
      domainName = args.origin.target.bucketRegionalDomainName;
      originId = args.origin.target.bucket;
      break;
    }
    case "custom-bucket-endpoint": {
      customErrorResponses = [{ errorCode: 404, responseCode: 200, responsePagePath: "/" }];
      domainName = args.origin.target.websiteEndpoint;
      originId = args.origin.target.websiteEndpoint;
      customOriginConfig = customOriginDefaults;
      customOriginConfig.originReadTimeout = originReadTimeout || 30;
      break;
    }
    case "custom": {
      customOriginConfig = customOriginDefaults;
      customOriginConfig.originReadTimeout = originReadTimeout || 30;
      domainName = args.origin.target.dnsName;
      originId = args.origin.target.name;
      break;
    }
  }

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
    defaultRootObject,
    webAclId,
    tags,
  });
}
